from colorama import Fore, Style
import json

from XAgent.utils import ToolCallStatusCode
from XAgent.engines.param_system import ParamSystem
from XAgent.tools.n8n_tools.n8n_compiler import n8n_compiler
from XAgent.tools.n8n_tools.n8n_runner import run_node
from XAgent.tools.n8n_tools.n8n_utils import n8nParamParseStatus
from XAgent.logs import logger


class n8nParamSystem(ParamSystem):
    

    def from_tool_name(self, tool_name):
        """从一个渠道load所有的可能参数
        """
        integration, resource, operation = tool_name.split(".")
        self.n8n_python_node = n8n_compiler.get_n8n_node(
            integration_name=integration,
            resource_name=resource,
            operation_name=operation
        )



    def partly_implement(self, given_param_dict):
        """允许用户去部分实现一些参数
        """
        logger.typewriter_log("prepare params for n8n node: ",Fore.BLUE, f"{self.n8n_python_node.node_meta.integration_name}.{self.n8n_python_node.node_meta.resource_name}.{self.n8n_python_node.node_meta.operation_name}")

        

        param_rewrite_status, output_str = self.n8n_python_node.parse_parameters(given_param_dict)
        print(param_rewrite_status)
        print(json.dumps(output_str,indent=2))
        if param_rewrite_status != n8nParamParseStatus.ParamParseSuccess:
            return param_rewrite_status, output_str

        return param_rewrite_status, output_str



    @property
    def param_sufficient(self):
        return True

    def to_description(self):
        """向语言模型描述待填写参数
        """
        pass


    def run_tool(self):
        params_json = {}
        for key, value in self.n8n_python_node.params.items():
            param = value.to_json()
            if param != None:
                params_json[key] = param
                
        logger.typewriter_log(
            "n8nTool: ",
            Fore.CYAN,
            f"COMMAND: {Fore.CYAN}{self.n8n_python_node.node_meta.integration_name}.{self.n8n_python_node.node_meta.resource_name}.{self.n8n_python_node.node_meta.operation_name}{Style.RESET_ALL}"
            f"ARGUMENTS: \n{Fore.CYAN}{json.dumps(params_json)}{Style.RESET_ALL}",
        )

        output_data,error = run_node(self.n8n_python_node)
        return output_data, ToolCallStatusCode.TOOL_CALL_SUCCESS