import json
from colorama import Fore, Style

from XAgent.utils import ToolCallStatusCode
from XAgent.tools import reacttoolexecutor
from XAgent.data_structure import ToolNode
from XAgent.tools.param_system import ParamSystem
from XAgent.logs import logger


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
        tool_node = ToolNode()
        tool_node.tool_name = self.tool_name
        tool_node.tool_args = self.params
        status_code,tool_output = reacttoolexecutor.execute(tool_node)

        return tool_output, status_code