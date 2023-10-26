from typing import Any,Union,Tuple
import json
from colorama import Fore, Style

from XAgent.ai_functions import function_manager
from XAgent.enums import ToolCallStatusCode
from XAgent.logs import logger
from .base import BaseToolInterface
from .n8n_tools.n8n_compiler import n8nCompiler
from .n8n_tools.n8n_utils import n8nParamParseStatus
from .n8n_tools.n8n_runner import run_node


class n8nToolInterface(BaseToolInterface):
    """
    Run n8n tools.
    """
    def __init__(self,*args,**kwargs) -> None:
        pass
        
    def lazy_init(self,config):
        self.n8n_compiler = n8nCompiler(config) 
        return self
    
    def close(self):
        pass
    
    def get_available_tools(self)->Tuple[list[str],dict]:
        return self.n8n_compiler.get_available_tools()
    
    def retrieve_tools(self, query:str, top_k:int=10)->dict:
        pass
    
    def get_schema_for_tools(self, tools: list[str], schema_type: str = "json"):
        if schema_type == "json":
            tools_json = []
            missing_tools = []
            for tool in tools:
                try:
                    tools_json.append(function_manager.get_function_schema(tool))
                except:
                    missing_tools.append(tool)
            return {
                'tools_json':tools_json,
                'missing_tools':missing_tools,
            }
        else:
            raise NotImplementedError
    
    def execute(self, tool_name:str, **kwargs)->Tuple[ToolCallStatusCode,Any]:
        integration_name, resource_name, operation_name = tool_name.split(".")
        n8n_node = self.n8n_compiler.get_n8n_node(integration_name, resource_name, operation_name)
        logger.typewriter_log("prepare params for n8n node: ",Fore.BLUE, f"{n8n_node.node_meta.integration_name}.{n8n_node.node_meta.resource_name}.{n8n_node.node_meta.operation_name}")
        param_rewrite_status, parse_output = n8n_node.parse_parameters(kwargs)

        if param_rewrite_status != n8nParamParseStatus.ParamParseSuccess:
            logger.typewriter_log("param parse error", Fore.RED, f"{param_rewrite_status.name}: {json.dumps(parse_output)}")
        
        params_json = {}
        for key, value in n8n_node.params.items():
            param = value.to_json()
            if param != None:
                params_json[key] = param
                
        logger.typewriter_log(
            "n8nTool: ",
            Fore.CYAN,
            f"COMMAND: {Fore.CYAN}{n8n_node.node_meta.integration_name}.{n8n_node.node_meta.resource_name}.{n8n_node.node_meta.operation_name}{Style.RESET_ALL}"
            f"ARGUMENTS: \n{Fore.CYAN}{json.dumps(params_json)}{Style.RESET_ALL}",
        )

        n8n_execution_data,error = run_node(n8n_node)
        
        return ToolCallStatusCode.TOOL_CALL_SUCCESS, n8n_execution_data