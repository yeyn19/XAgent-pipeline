from colorama import Fore,Style
from typing import Any,Union,Tuple

from XAgent.logs import logger
from XAgent.config import CONFIG
from XAgent.data_structure import ToolNode,ToolType
from XAgent.tools.interface import BaseToolInterface
from XAgent.utils import ToolCallStatusCode

class BaseToolExecutor:
    """原子Tool调用可以用默认的executor
    """
    def __init__(self,config=CONFIG) -> None:
        self.config = config
        self.interfaces:dict[ToolType,BaseToolInterface] = {}
    
    def lazy_init(self,config=CONFIG):
        self.config = config
    
    def set_interface_for_type(self,tool_type:ToolType,interface:BaseToolInterface):
        self.interfaces[tool_type] = interface
        
    def get_interface_for_type(self,tool_type:ToolType,)->BaseToolInterface:
        return self.interfaces[tool_type]
    
    def close(self):
        for interface in self.interfaces.values():
            interface.close()
    
    def get_available_tools(self)->Tuple[list[str],dict]:
        """flatten所有interface和对应的tool
        """
        available_tools = []
        tools_json = []
        tool_type_mapping = {}
        for tool_type,interface in self.interfaces.items():
            new_tools,new_tools_json = interface.get_available_tools()
            for tool in new_tools:
                tool_type_mapping[tool] = tool_type
            available_tools.extend(new_tools)
            tools_json.extend(new_tools_json)
        self.tool_type_mapping = tool_type_mapping
        return available_tools,tools_json
    
    def execute(self,tool_node:ToolNode)->Tuple[ToolCallStatusCode,Any]:
        """执行一个toolNode，返回对应的执行状态码和data
        """
        logger.typewriter_log(
            "NEXT ACTION: ",
            Fore.CYAN,
            f"TOOL: {Fore.CYAN}{tool_node.tool_name}{Style.RESET_ALL}  \n"
            f"ARGUMENTS: \n{Fore.CYAN}{tool_node.tool_args}{Style.RESET_ALL}",
        )
        
        if (interface:=self.interfaces.get(tool_node.tool_type,None)) is None:
            interface = self.interfaces[self.tool_type_mapping[tool_node.tool_name]]
        status_code,output = interface.execute(tool_node.tool_name,**tool_node.tool_args)
        
        tool_node.data['tool_output'] = output
        tool_node.data['tool_status_code'] = status_code
        
        logger.typewriter_log("Tool Return: ", Fore.YELLOW, str(output))
        logger.typewriter_log(
            "TOOL STATUS CODE: ", Fore.YELLOW, f"{status_code.color()}{status_code.name}{Style.RESET_ALL}"
        )
        return status_code,output
