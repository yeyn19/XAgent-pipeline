from colorama import Fore

from XAgent.logs import logger
from XAgent.tools import ReActToolExecutor
from XAgent.message_history import Message
from XAgent.agent.summarize import summarize_action,summarize_plan,clip_text
from XAgent.global_vars import INTERRUPT

from .base import BaseEngine,ExecutionNode,ExecutionGraph

class ReActEngine(BaseEngine):
    
    
    async def step(self,
                   task,
                   
                   plans:dict,
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
        
        if interrupt:
            logger.typewriter_log(
                "INTERRUPTED",
                Fore.RED,
                "",
            )
            from XAgent.global_vars import INTERRUPT_MESSAGE
            # TODO: add interrupt message
            # message:str = await INTERRUPT_MESSAGE.get()
        
        
        if self.config.enable_summary:
            task = summarize_plan(task)
        
        
        action_history = summarize_action(toolexecutor.action_history)
        
        messages = [
            Message("user", f'''Now you will perform the following subtask:\n"""\n{task}\n"""\n'''),
            Message("user", f"""The following steps have been performed (you have already done the following and the current file contents are shown below):\n{action_history}"""),
        ]
        
        self.config
        
    async def run(self,task,*args,**kwargs)->ExecutionGraph:
        """Execute the engine and return the result node."""
        execution_trace = ExecutionGraph()
        begin_node = ExecutionNode(begin_node=True)
        execution_trace.set_begin_node(begin_node)
        
        
        node = begin_node
        while node.end_node != False:
            nnode = await self.step(
                task=task,
                force_stop = execution_trace.node_count >= self.config.max_subtask_chain_length,
                interrupt = INTERRUPT,
                *args,**kwargs)
            
            execution_trace.add_node(nnode)
            execution_trace.add_edge(node,nnode)
            node = nnode
            
            
        execution_trace.set_end_node(node)
        
        return execution_trace