from colorama import Fore

from XAgent.logs import logger
from XAgent.models import ExecutionNode
from XAgent.tools import ReActToolExecutor

from .base import BaseEngine

class ReActEngine(BaseEngine):
    
    
    async def step(self,
                   toolexecutor:ReActToolExecutor,
                   force_stop:bool=False,
                   interrupt:bool=False,
                   *args,**kwargs)->ExecutionNode:
        """Step and return execution result."""    
        logger.typewriter_log(
            "-=-=-=-=-=-=-= THOUGHTS, REASONING, PLAN AND CRITICISM WILL NOW BE VERIFIED BY AGENT -=-=-=-=-=-=-=",
            Fore.GREEN,
            "",
        )
        
            
        
        
        