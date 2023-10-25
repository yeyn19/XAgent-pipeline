from typing import Any,Tuple

from XAgent.config import CONFIG
from XAgent.models import ExecutionNode,TaskSearchTree
from XAgent.global_vars import INTERRUPT


class BaseEngine:
    """The Engine is the core of XAgent, it is responsible to manage the workflow of the XAgent and determine the execution order of the tools."""
    def __init__(self, config=CONFIG):
        self.config = config
    
    
    async def step(self,*args,**kwargs)->bool:
        """Step and return whether the engine should continue."""
        raise NotImplementedError
    
    async def run(self,*args,**kwargs)->ExecutionNode:
        """Execute the engine and return the result node."""
        execution_trace = TaskSearchTree()
        