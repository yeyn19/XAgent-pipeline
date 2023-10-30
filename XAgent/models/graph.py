import uuid
import random
from pydantic import BaseModel,Field
from typing import Dict,Any,Optional,Union,List

from XAgent.enums import EngineExecutionStatusCode
from .plan import Plan
from .node import ToolCall

GID = str

def assign_gid()->GID:
    return str(uuid.uuid4())

class ExecutionNode(BaseModel):
    node_id:GID = Field(default_factory=assign_gid)
    in_degree:int = 0
    out_degree:int = 0
    tool_call:ToolCall = None
    
    begin_node:bool = False
    end_node:bool = False
    
    def __eq__(self, other) -> bool:
        if isinstance(other,ExecutionNode):
            return self.node_id == other.node_id
        raise NotImplementedError('Unsupported operation between {} and {}'.format(type(self),type(other)))
    
    def __str__(self) -> str:
        return str(self.node_id)

class TaskNode(ExecutionNode):
    plan:Plan = None
    begin_node:bool = True

class DirectedEdge(BaseModel):
    edge_id:GID  = Field(default_factory=assign_gid)
    def __eq__(self, other) -> bool:
        if isinstance(other,DirectedEdge):
            return self.edge_id == other.edge_id
        raise NotImplementedError('Unsupported operation between {} and {}'.format(type(self),type(other)))
    
    def __str__(self) -> str:
        return str(self.edge_id)
    
class ExecutionGraph(BaseModel):
    begin_node:Optional[GID] = None
    end_node:Optional[GID] = None
    nodes:Dict[GID,ExecutionNode] = {}
    edges:Dict[GID,Dict[GID,DirectedEdge]] = {}
    status:EngineExecutionStatusCode = EngineExecutionStatusCode.DOING

    def convert_to_dict(self):
        data = []
        all_start_nodes = [node.node_id for node in self.nodes.values() if node.in_degree == 0]
        all_visited_nodes = set()
        for node in all_start_nodes:
            def dfs(node:ExecutionNode)->Dict[Any,Any]:
                if node.node_id in all_visited_nodes:
                    return None
                all_visited_nodes.add(node.node_id)
                node_json = node.model_dump()
                for next_node in self.get_adjacent_node(node):
                    next_node_dict = dfs(self.nodes[next_node])
                    if next_node_dict is not None:
                        node_json['next'].append(next_node_dict)
                return node_json
            
            data.append(dfs(self.nodes[node]))
        
        return data
    
    def get_execution_track(self,exclude_begin_node=True):
        sequence = []
        all_start_nodes = [node.node_id for node in self.nodes.values() if node.in_degree == 0]
        all_visited_nodes = set()
        for node in all_start_nodes:
            def dfs(node:ExecutionNode)->Dict[Any,Any]:
                if node.node_id in all_visited_nodes:
                    return
                all_visited_nodes.add(node.node_id)
                sequence.append(node)
                for next_node in self.get_adjacent_node(node):
                    dfs(self.nodes[next_node])
            dfs(self.nodes[node])
        
        if exclude_begin_node:
            sequence = list(filter(lambda x:x.node_id not in all_start_nodes,sequence))
        return sequence
    
    def reduce_graph_to_sequence(self):
        # random walk to a leaf node
        eg = ExecutionGraph()
        node = self.nodes[self.begin_node]
        eg.set_begin_node(node)
        last_node = node
        adj_nodes = self.get_adjacent_node(node)
        while len(adj_nodes)>0:
            node = self.nodes[random.choice(adj_nodes)]
            adj_nodes = self.get_adjacent_node(node)
            eg.add_node(node)
            eg[last_node,node] = None
            last_node = node
        return eg

    @property
    def node_count(self):
        return len(self.nodes.keys())
    @property
    def edge_count(self):
        count = 0
        for k,d in self.edges.items():
            count += len(d.keys())
        return count
    
    def set_begin_node(self,node:Union[GID,ExecutionNode]):
        if isinstance(node,ExecutionNode):
            self.begin_node = node.node_id
            if node.node_id not in self.nodes:
                self.nodes[node.node_id] = node
        elif isinstance(node,GID):
            if node not in self.nodes:
                raise KeyError('node not in graph!')
            else:
                self.begin_node = node
        else:
            raise TypeError(f'Unknown node type: {type(node)}，node must be instance of ExecutionNode!')
        
    def get_begin_node(self):
        return self.nodes[self.begin_node]
    
    
    def set_end_node(self,node:Union[GID,ExecutionNode]):
        if isinstance(node,ExecutionNode):
            self.end_node = node.node_id
            if node.node_id not in self.nodes:
                self.nodes[node.node_id] = node
        elif isinstance(node,GID):
            if node not in self.nodes:
                raise KeyError('node not in graph!')
            else:
                self.end_node = node
        else:
            raise TypeError('node must be instance of ExecutionNode!')
        
    def get_end_node(self):
        return self.nodes[self.end_node]
    
    def add_node(self,node:ExecutionNode):
        if isinstance(node,ExecutionNode):
            self.nodes[node.node_id] = node
        else:
            raise TypeError('node must be instance of ExecutionNode!')
    
    def add_edge(self,from_node:Union[ExecutionNode,GID],to_node:Union[ExecutionNode,GID],edge:DirectedEdge=None):
        if isinstance(from_node,ExecutionNode):
            from_node = from_node.node_id
        if isinstance(to_node,ExecutionNode):
            to_node = to_node.node_id
        if from_node not in self.edges:
            self.edges[from_node] = {}
        if edge is None:
            self.edges[from_node][to_node] = DirectedEdge()
        else:
            if isinstance(edge,DirectedEdge):
                self.edges[from_node][to_node] = edge
            else:
                raise TypeError('edge must be instance of DirectedEdge!')
        self.nodes[to_node].in_degree += 1
        self.nodes[from_node].out_degree +=1

        
    def pop_node(self,node:Union[ExecutionNode,GID])->Union[ExecutionNode,None]:
        if isinstance(node,ExecutionNode):
            node = node.node_id
        return self.nodes.pop(node,None)
        
    def pop_edge(self,from_node:Union[ExecutionNode,GID],to_node:Union[ExecutionNode,GID])->Union[DirectedEdge,None]:
        if isinstance(from_node,ExecutionNode):
            from_node = from_node.node_id
        if isinstance(to_node,ExecutionNode):
            to_node = to_node.node_id
        if from_node in self.edges:
            return self.edges[from_node].pop(to_node,None)
        return None
    
    def get_adjacent_node(self,node:Union[ExecutionNode,GID])->List[GID]:
        if isinstance(node,ExecutionNode):
            node = node.node_id
        return list(self.edges.get(node,{}).keys())
    
    def get_edge_nodes(self, DirectedEdge):
        for from_node_id in self.edges.keys():
            for to_node_id in self.edges[from_node_id].keys():
                if self.edges[from_node_id][to_node_id] == DirectedEdge:
                    return self[from_node_id], self[to_node_id]
        
    def __getitem__(self, item)->Union[ExecutionNode,DirectedEdge]:
        if isinstance(item, GID):
            return self.nodes[item]
        elif isinstance(item, tuple) and len(item) == 2:
            k1,k2 = item
            if isinstance(k1,ExecutionNode):
                k1 = k1.node_id
            if isinstance(k2,ExecutionNode):
                k2 = k2.node_id
            
            if isinstance(k1,GID) and isinstance(k2,GID):
                return self.edges[k1][k2]
            else:
                raise TypeError('key must be GID or ExecutionNode!')
        else:
            raise IndexError("Invalid number of arguments")
    
    def __setitem__(self,key,value):
        if len(key)==0:
            self.add_node(value)
        elif isinstance(key, GID):
            if isinstance(value,ExecutionNode):
                value.node_id = key
                self.nodes[key] = value
            else:
                raise TypeError('node must be instance of ExecutionNode!')
            
        elif isinstance(key, tuple) and len(key) == 2:
            self.add_edge(key[0],key[1],value)
        else:
            raise IndexError("Invalid number of arguments")