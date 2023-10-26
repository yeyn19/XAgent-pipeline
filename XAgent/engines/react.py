from colorama import Fore
from XAgent.config import CONFIG

from XAgent.logs import logger,print_assistant_thoughts
from XAgent.agent.summarize import summarize_action,summarize_plan,clip_text
from XAgent.global_vars import INTERRUPT,agent_dispatcher
from XAgent.ai_functions import function_manager
from XAgent.tools import ToolServerInterface,BuiltInInterface

from XAgent.models import ReActExecutionNode,ReActExecutionGraph
from XAgent.enums import RequiredAbilities,EngineExecutionStatusCode,ToolCallStatusCode
from XAgent.message_history import Message

from .base import BaseEngine,TaskNode

class ReActEngine(BaseEngine):
    def __init__(self, config=CONFIG):
        super().__init__(config)
        
        self.agent = agent_dispatcher.dispatch(RequiredAbilities.tool_tree_search,None)
        
        self.toolserverif = ToolServerInterface()
        self.builtinif = BuiltInInterface()
        self.toolifs = [self.toolserverif,self.builtinif]
        
        
    async def step(self,
                   task:dict,
                   past_steps:list[ReActExecutionNode],
                   plans:dict = None,
                   functions:list[dict]=[],
                   force_stop:bool=False,
                   interrupt:bool=False,
                   finish_tool_call:str='subtask_submit',
                   **kwargs)->ReActExecutionNode:
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
        
        task_id = task['task_id']
        if self.config.enable_summary:
            task = summarize_plan(task)
            if plans is not None:
                plans = summarize_plan(plans)
        
        
        step_summary = summarize_action(list(map(lambda x:x.tool_call.data,past_steps)),task)
        
        messages = [
            Message("user", f'''Now you will perform the following subtask:\n{task}'''),
            Message("user", f'''The following steps have been performed (you have already done the following and the current file contents are shown below):\n{step_summary}'''),
        ]
        human_prompt = ""
        if self.config.enable_ask_human_for_help:
            human_prompt = "- Use 'ask_human_for_help' when you need help, remember to be specific to your requirement to help user to understand your problem."
        else:
            human_prompt = "- Human is not avaliable for help. You are not allowed to ask human for help in any form or channel. Solve the problem by yourself. If information is not enough, try your best to use default value."
        
        _,file_archi = self.toolserverif.execute("FileSystemEnv_print_filesys_struture",return_root=True)
        file_archi,_ = clip_text(file_archi,1000,clip_end=True)
        
        message,_ = self.agent.parse(
            placeholders={
                "system": {
                    "all_plan": plans if plans is not None else "**No other plan**",
                },
                "user": {
                    "workspace_files":file_archi,
                    "subtask_id": task_id,
                    "max_length": self.config.max_subtask_chain_length,
                    "step_num": len(past_steps),
                    "human_help_prompt": human_prompt,
                }
            },
            arguments=function_manager.get_function_schema('action_reasoning')['parameters'],
            functions=self.tools_schema+functions,
            function_call={'name':finish_tool_call} if force_stop else None,
            additional_messages=messages,
            additional_insert_index=-1
        )
        
        
        exec_node = ReActExecutionNode(tool_call=self.agent.message_to_tool_node(message))
        
        thoughts = print_assistant_thoughts(exec_node.tool_call.data, False)

        status_code,tool_output = await self.execute(exec_node.tool_call)
        
        exec_node.status_code = status_code
        if exec_node.tool_call.tool_name == finish_tool_call:
            exec_node.end_node = True
        
        # transmit infomations
        await kwargs['interaction'].update_cache(update_data={**thoughts, "using_tools": {
            "tool_name": exec_node.tool_call.tool_name,
            "tool_input": exec_node.tool_call.tool_args,
            "tool_output": tool_output,
            "tool_status_code": status_code.name,
            "thought_data": {
                "thought": exec_node.tool_call.thought, 
                "content": exec_node.tool_call.content
            }
        }}, status="inner", current=task_id)

        return exec_node
        
        
        
    async def run(self,task:TaskNode,**kwargs)->ReActExecutionGraph:
        """Execute the engine and return the result node."""
        execution_track = ReActExecutionGraph()
        execution_track.set_begin_node(task)
        
        await self.get_available_tools()
        
        node = task
        while not node.end_node:
            nnode = await self.step(
                task=task.plan.to_json(posterior=False),
                past_steps=execution_track.get_execution_track(),
                force_stop = execution_track.node_count >= self.config.max_subtask_chain_length,
                interrupt = INTERRUPT,
                **kwargs)
            
            execution_track.add_node(nnode)
            execution_track.add_edge(node,nnode)
            node = nnode
        
        if node.status_code == ToolCallStatusCode.SUBMIT_AS_SUCCESS:
            execution_track.status = EngineExecutionStatusCode.SUCCESS
        else:
            execution_track.status = EngineExecutionStatusCode.FAIL

        execution_track.set_end_node(node)
                
        return execution_track