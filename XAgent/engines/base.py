from typing import Any,Tuple

from XAgent.config import CONFIG
from XAgent.models import ExecutionNode,ExecutionGraph
from XAgent.global_vars import INTERRUPT


class BaseEngine:
    """The Engine is the core of XAgent, it is responsible to manage the workflow of the XAgent and determine the execution order of the tools."""
    def __init__(self, config=CONFIG):
        self.config = config
    
    
    async def step(self,*args,**kwargs)->ExecutionNode:
        """Step and return execution result."""
        raise NotImplementedError
    
    async def run(self,*args,**kwargs)->ExecutionGraph:
        """Execute the engine and return the result node."""
        execution_trace = ExecutionGraph()
        begin_node = ExecutionNode(begin_node=True)
        
        node = begin_node
        while node.end_node != False:
            nnode = await self.step(*args,**kwargs)
            
            execution_trace.add_node(nnode)
            execution_trace.add_edge(node,nnode)
            node = nnode
            
            # check interrupt
            if INTERRUPT:
                break
            
        return execution_trace
        
        
        
        
        