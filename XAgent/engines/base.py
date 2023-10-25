from typing import Any,Tuple

from XAgent.config import CONFIG
from XAgent.models import ExecutionNode,ExecutionGraph


class BaseEngine:
    """The Engine is the core of XAgent, it is responsible to manage the workflow of the XAgent and determine the execution order of the tools."""
    def __init__(self, config=CONFIG):
        self.config = config
    
    
    async def step(self,
                   task,
                   plans:dict,
                   force_stop:bool=False,
                   interrupt:bool=False,
                   *args,**kwargs)->ExecutionNode:
        """Step and return execution result."""
        raise NotImplementedError
    
    async def run(self,task,*args,**kwargs)->ExecutionGraph:
        """Execute the engine and return the result node."""
        raise NotImplementedError
        
        
        
        
        