"""node里存储运行时信息
"""
from __future__ import annotations
from typing import List, Optional, Any
from colorama import Fore, Style
from dataclasses import dataclass, field
import importlib
import uuid
import types

from XAgent.utils import AutoMatEdgeType, AutoMatStateChangeHardness,ExecutionType, ToolCallStatusCode
from XAgent.tools.param_system import ParamSystem
from XAgent.logs import logger





@dataclass
class PipelineAutoMatNode():
    """一个自动机节点"""
    node_name: str
    tool_name: str
    node_type: ExecutionNodeType
    state_change_hardness: AutoMatStateChangeHardness = AutoMatStateChangeHardness.GPT4

    """存储该节点在运行时的访问情况"""
    runtime_stack: List[RuntimeNode] = field(default_factory=list)

    out_edges: List["PipelineAutoMatEdge"] = field(default_factory=list)
    
    @staticmethod
    def from_json(node):
        new_node = PipelineAutoMatNode(
                        node_name=node["node_name"],
                        tool_name=node["tool_name"],
                        node_type=ExecutionNodeType(node["node_type"]),
                    )
        # TODO: other params?
        return new_node

    @staticmethod
    def get_defualt_ReACT_node():
        """对于所有节点默认添加一个ReACT-node作为指向的节点，来处理异常情况
        """
        new_node = PipelineAutoMatNode(
                        node_name=uuid.uuid1(),
                        tool_name="",
                        node_type=ExecutionNodeType.ReACT,
                    )
        # TODO: other params?
        return new_node



@dataclass
class PipelineAutoMatEdge():
    edge_name: str
    from_node: Optional[PipelineAutoMatNode] = None
    to_node: Optional[PipelineAutoMatNode] = None

    comments: List[str] = field(default_factory=List)

    def get_defualt_ReACT_branch(from_node: PipelineAutoMatNode):
        react_node = PipelineAutoMatNode.get_defualt_ReACT_node()
        new_edge = PipelineAutoMatEdge(
            edge_name=f"exception_edge_for_{from_node.node_name}",
            from_node=from_node,
            to_node=react_node,
            comments=[
                "the default edge to handle exception: route to this edge when all other conditions didn't happen"
            ]
        )

        return new_edge

    def to_json(self):
        pass



@dataclass
class PipelineMeta():
    name: str
    purpose: str
    author: str

    params: dict
    
    @staticmethod
    def from_json(meta_data):
        return PipelineMeta(
            name=meta_data["name"],
            purpose=meta_data["purpose"],
            author=meta_data["author"],
            params = meta_data["params"]
        )

class PipelineAutoMat():
    """用一个自动机来描述pipeline，是一种动态的RPA方法，每次的选边都由模型来完成。
    同时需要维护一个运行时的调用栈
    
    """
    def __init__(self):
        self.start_node: PipelineAutoMatNode = None
        self.nodes: List[PipelineAutoMatNode] = []
        self.runtime_info: RuntimeStackUserInterface = RuntimeStackUserInterface() #存储自动机的运行时信息

        self.meta: PipelineMeta = None


    @staticmethod
    def from_json(json_data: dict, rule_file_name:str):
        automat = PipelineAutoMat()
        automat.meta = PipelineMeta.from_json(json_data["meta"])
        for node in json_data["nodes"]:
            new_node = PipelineAutoMatNode.from_json(node)
            from XAgent.tools.param_system_interface import get_param_system
            new_node.param_interface = get_param_system(new_node.tool_name, new_node.node_type)

            function_name = f"route_node_{new_node.node_name}"
            module = importlib.import_module(rule_file_name)
            # 检查函数是否存在
            if hasattr(module, function_name):
                # 获取函数并将其绑定为实例方法
                func = getattr(module, function_name)
                new_node.route = types.MethodType(func, new_node)
                logger.typewriter_log(f"node \"{new_node.node_name}\"({new_node.tool_name}):",Fore.BLUE, "find existing route-function")
            else:
                logger.typewriter_log(f"node \"{new_node.node_name}\"({new_node.tool_name}):",Fore.BLUE, "use default route-function")

            automat.nodes.append(new_node)
            if new_node.node_type == ExecutionNodeType.Controlflow and new_node.tool_name == "start":
                automat.start_node = new_node
            
        for edge in json_data["edges"]:
            edge_data = PipelineAutoMatEdge(
                edge_name=edge["edge_name"],
                comments=edge["comments"],
            )
            from_name = edge["from_node"]
            to_name = edge["to_node"]
            for node in automat.nodes:
                if node.node_name == from_name:
                    edge_data.from_node = node
                if node.node_name == to_name:
                    edge_data.to_node = node
            if edge_data.from_node == None or edge_data.to_node == None:
                raise NotImplementedError

            function_name = f"route_edge_{edge_data.edge_name}"
            module = importlib.import_module(rule_file_name)
            # 检查函数是否存在
            if hasattr(module, function_name):
                # 获取函数并将其绑定为实例方法
                func = getattr(module, function_name)
                edge_data.route = types.MethodType(func, edge_data)
                logger.typewriter_log(f"edge \"{edge_data.edge_name}\"({edge_data.from_node.node_name} -> {edge_data.to_node.node_name}):",Fore.BLUE, "find existing route-function")
            else:
                logger.typewriter_log(f"edge \"{edge_data.edge_name}\"({edge_data.from_node.node_name} -> {edge_data.to_node.node_name}):",Fore.BLUE,  "use default route-function")
        
            
            edge_data.from_node.out_edges.append(edge_data)

        for node in automat.nodes:
            node.out_edges.append(PipelineAutoMatEdge.get_defualt_ReACT_branch(from_node=node))
        return automat


@dataclass
class RouteResult():
    select_node: PipelineAutoMatNode
    select_edge: PipelineAutoMatEdge
    params: dict
    param_sufficient: bool