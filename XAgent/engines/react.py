from colorama import Fore

from XAgent.logs import logger,print_assistant_thoughts
from XAgent.tools import ReActToolExecutor
from XAgent.models import ToolNode
from XAgent.enums import RequiredAbilities,ToolType,SearchMethodStatusCode,ToolCallStatusCode
from XAgent.message_history import Message
from XAgent.agent.summarize import summarize_action,summarize_plan,clip_text
from XAgent.global_vars import INTERRUPT,agent_dispatcher

from .base import BaseEngine,ExecutionNode,ExecutionGraph

class ToolExecutionNode(ExecutionNode):
    tool_call:ToolNode = None
    status_code:ToolCallStatusCode = ToolCallStatusCode.OTHER_ERROR
    
    
class ReActExecutionGraph(ExecutionGraph):
    status:SearchMethodStatusCode = SearchMethodStatusCode.DOING
    need_for_plan_refine:bool = False

    
class ReActEngine(BaseEngine):
    
    async def step(self,
                   task,
                   past_steps:list[ToolExecutionNode],
                   plans:dict,
                   arguments,
                   functions:dict,
                   toolexecutor:ReActToolExecutor,
                   force_stop:bool=False,
                   interrupt:bool=False,
                   finish_tool_call:str='subtask_submit',
                   *args,**kwargs)->ToolExecutionNode:
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
        
        _,file_archi = toolexecutor.get_interface_for_type(ToolType.ToolServer).execute("FileSystemEnv_print_filesys_struture",return_root=True)
        file_archi,_ = clip_text(file_archi,1000,clip_end=True)
        
        
        agent = agent_dispatcher.dispatch(RequiredAbilities.tool_tree_search,task)
        
        message,_ = agent.parse(
            placeholders={
                "system": {
                    "all_plan": plans
                },
                "user": {
                    "workspace_files":file_archi,
                    "subtask_id": task_id,
                    "max_length": self.config.max_subtask_chain_length,
                    "step_num": len(past_steps),
                    "human_help_prompt": human_prompt,
                }
            },
            arguments=arguments,
            functions=functions,
            function_call={'name':finish_tool_call} if force_stop else None, # TODO: should change to a variable in future
            additional_messages=messages,
            additional_insert_index=-1
        )
        
        exec_node = ToolExecutionNode(tool_call=agent.message_to_tool_node(message))
        status_code,tool_output = toolexecutor.execute(exec_node.tool_call)
        
        exec_node.status_code = status_code
        if exec_node.tool_call.tool_name == finish_tool_call:
            exec_node.end_node = True
        
        # transmit infomations
        await kwargs['interaction'].update_cache(update_data={**print_assistant_thoughts(exec_node.tool_call.data, False), "using_tools": {
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
        
        
        
    async def run(self,task,plans,*args,**kwargs)->ReActExecutionGraph:
        """Execute the engine and return the result node."""
        execution_track = ReActExecutionGraph()
        begin_node = ExecutionNode(begin_node=True)
        execution_track.set_begin_node(begin_node)
        
        
        node = begin_node
        while not node.end_node:
            nnode = await self.step(
                task=task,
                past_steps=execution_track.get_execution_track(),
                plans=plans,
                force_stop = execution_track.node_count >= self.config.max_subtask_chain_length,
                interrupt = INTERRUPT,
                *args,**kwargs)
            
            execution_track.add_node(nnode)
            execution_track.add_edge(node,nnode)
            node = nnode
        
        if node.status_code == ToolCallStatusCode.SUBMIT_AS_SUCCESS:
            execution_track.status = SearchMethodStatusCode.SUCCESS
        else:
            execution_track.status = SearchMethodStatusCode.FAIL

        execution_track.set_end_node(node)
                
        return execution_track