import json
from colorama import Fore, Style

from XAgent.utils import ToolCallStatusCode
from XAgent.tools.XAgent_tools.tool_call_handle import toolserver_interface
from XAgent.tools.param_system import ParamSystem
from XAgent.loggers.logs import logger


class XAgentParamSystem(ParamSystem):
    

    def from_tool_name(self, tool_name):
        self.tool_name = tool_name


    def partly_implement(self, given_param_dict):
        self.params = given_param_dict

    @property
    def param_sufficient(self):
        """检测已提供参数是否可以正确执行工具
        """
        return True

    def to_description(self):
        """向语言模型描述待填写参数
        """
        pass


    def run_tool(self):
        logger.typewriter_log(
            "XAgentTool: ",
            Fore.CYAN,
            f"COMMAND: {Fore.CYAN}{self.tool_name}{Style.RESET_ALL}  \n"
            f"ARGUMENTS: \n{Fore.CYAN}{json.dumps(self.params)}{Style.RESET_ALL}",
        )

        command_result, tool_output_status_code = toolserver_interface.execute_command_client(
            command_name=self.tool_name,
            arguments=self.params
        )
        MAX_RETRY = 10
        retry_time = 0
        while retry_time<MAX_RETRY and tool_output_status_code == ToolCallStatusCode.TIMEOUT_ERROR and isinstance(command_result['detail'],dict) and 'type' in command_result['detail'] and command_result['detail']['type']=='retry':
            time.sleep(3)
            retry_time += 1
            command_result, tool_output_status_code, = toolserver_interface.execute_command_client(
                command_result['detail']['next_calling'],
                command_result['detail']['arguments'],
            )

        if tool_output_status_code == ToolCallStatusCode.TIMEOUT_ERROR and retry_time==MAX_RETRY:
            command_result = "Timeout and no content returned! Please check the content you submit!"

        return command_result, tool_output_status_code