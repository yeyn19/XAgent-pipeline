from typing import Any,Tuple

from XAgent.config import CONFIG
from XAgent.models import ExecutionNode,ExecutionGraph
from XAgent.global_vars import INTERRUPT


class BaseEngine:
    """The Engine is the core of XAgent, it is responsible to manage the workflow of the XAgent and determine the execution order of the tools."""
    def __init__(self, config=CONFIG):
        self.config = config
    
    
    async def step(self,force_stop:bool=False,*args,**kwargs)->ExecutionNode:
        """Step and return execution result."""
        raise NotImplementedError
    
    async def run(self,*args,**kwargs)->ExecutionGraph:
        """Execute the engine and return the result node."""
        execution_trace = ExecutionGraph()
        begin_node = ExecutionNode(begin_node=True)
        execution_trace.set_begin_node(begin_node)
        
        
        node = begin_node
        while node.end_node != False:
            nnode = await self.step(
                force_stop = execution_trace.node_count >= self.config.max_subtask_chain_length,
                *args,**kwargs)
            
            execution_trace.add_node(nnode)
            execution_trace.add_edge(node,nnode)
            node = nnode
            
            # check interrupt
            if INTERRUPT:
                break
            
        execution_trace.set_end_node(node)
        
        return execution_trace
        
        
        
        
        