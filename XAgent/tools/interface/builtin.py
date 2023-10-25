import json
from typing import Any,Tuple
from colorama import Fore

from XAgent.logs import logger
from XAgent.ai_functions import function_manager
from XAgent.utils import ToolCallStatusCode
from .base import BaseToolInterface

class BuiltInInterface(BaseToolInterface):
    def lazy_init(self,config):
        self.config = config
        self.subtask_submit_function = function_manager.get_function_schema('subtask_submit')

        self.ask_human_for_help_function  = function_manager.get_function_schema('ask_human_for_help')
        self.human_interruption_function = function_manager.get_function_schema('human_interruption')
        return self
    
    def close(self):
        pass

    def get_available_tools(self) -> Tuple[list[str],dict]:
        tool_list = [self.subtask_submit_function]
        if self.config.enable_ask_human_for_help:
            tool_list.append(self.ask_human_for_help_function)
        return list(map(lambda x:x['name'],tool_list)),tool_list
        # return {
        #     'available_tools':list(map(lambda x:x['name'],tool_list)),
        #     'tools_json':tool_list
        # }

    def execute(self, tool_name: str, **kwargs) -> Any:
        match tool_name:
            case 'subtask_submit':
                return self.subtask_submit(kwargs)
            case 'ask_human_for_help':
                return self.human_help(kwargs)
            case _:
                raise KeyError(f'Tool: {tool_name} not found in BuiltInInterface')
            
    def human_help(self,kwargs):
        logger.typewriter_log(
            "ASK For Human Help",
            Fore.RED,
            "You must give some suggestions, please type in your feedback and then press 'Enter' to send and continue the loop"
        )
        human_suggestion = input()
        res = json.dumps({"output":f"{human_suggestion}"}, ensure_ascii=False)
        return  ToolCallStatusCode.TOOL_CALL_SUCCESS,res
    
    def subtask_submit(self,kwargs):
        if kwargs["result"]["success"]:
            status_code = ToolCallStatusCode.SUBMIT_AS_SUCCESS
        else:
            status_code = ToolCallStatusCode.SUBMIT_AS_FAILED
        res = {
            "content": f"you have successfully submit the subtask as {kwargs['submit_type']}"
        }
        self.log_task_submit(kwargs)

        return  status_code,res
    
    def log_task_submit(self, arguments):
        logger.typewriter_log(
            f"-=-=-=-=-=-=-= SUBTASK SUBMITED -=-=-=-=-=-=-=",
            Fore.YELLOW,
            "",
        )
        logger.typewriter_log(
            f"submit_type:", Fore.YELLOW, f"{arguments['submit_type']}"
        )
        logger.typewriter_log(
            f"success:", Fore.YELLOW, f"{arguments['result']['success']}"
        )
        logger.typewriter_log(
            f"conclusion:", Fore.YELLOW, f"{arguments['result']['conclusion']}"
        )
        if "milestones" in arguments["result"].keys():
            logger.typewriter_log(
                f"milestones:", Fore.YELLOW
            )
            for milestone in arguments["result"]["milestones"]:
                line = milestone.lstrip("- ")
                logger.typewriter_log("- ", Fore.GREEN, line.strip())
        logger.typewriter_log(
            f"need_for_plan_refine:", Fore.YELLOW, f"{arguments['suggestions_for_latter_subtasks_plan']['need_for_plan_refine']}"
        )
        logger.typewriter_log(
            f"plan_suggestions:", Fore.YELLOW, f"{arguments['suggestions_for_latter_subtasks_plan']['reason']}"
        )