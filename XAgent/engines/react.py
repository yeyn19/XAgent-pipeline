from colorama import Fore

from XAgent.logs import logger
from XAgent.models import ExecutionNode
from XAgent.tools import ReActToolExecutor

from .base import BaseEngine

class ReActEngine(BaseEngine):
    
    async def run(self,toolexecutor:ReActToolExecutor,*args,**kwargs)->ExecutionNode:
        action_nodes = []
        
        while len(action_nodes) < self.config.max_subtask_chain_length:
            logger.typewriter_log(
                "-=-=-=-=-=-=-= THOUGHTS, REASONING, PLAN AND CRITICISM WILL NOW BE VERIFIED BY AGENT -=-=-=-=-=-=-=",
                Fore.GREEN,
                "",
            )
            
            # check interrupt
            
        
        
            action_nodes.append(node)
        