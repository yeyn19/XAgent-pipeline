from typing import Any,Tuple
from colorama import Fore,Style

from XAgent.logs import logger
from XAgent.config import CONFIG
from XAgent.models import ExecutionNode,ExecutionGraph,ToolCall,TaskNode
from XAgent.enums import ToolCallStatusCode
from XAgent.tools import BaseToolInterface


class BaseEngine:
    """The Engine is the core of XAgent, it is responsible to manage the workflow of the XAgent and determine the execution order of the tools."""
    def __init__(self, config=CONFIG):
        self.config = config
        self.toolifs:list[BaseToolInterface] = []
        self.toolif_mapping:dict[str,BaseToolInterface]  = {}
        self.available_tools:list[str] = []
        self.tools_schema:list[dict] = []
        
    async def lazy_init(self,config=None):
        if config is not None:
            self.config = config        
        await self.get_available_tools()
        
    async def get_available_tools(self)->Tuple[list[str],list[dict]]:
        self.available_tools = []
        self.tools_schema = []
        self.toolif_mapping = {}
        
        for interface in self.toolifs:
            interface.lazy_init(self.config)
            tools,tools_json = interface.get_available_tools()
            self.available_tools.extend(tools)
            self.tools_schema.extend(tools_json)
            for tool in tools:
                self.toolif_mapping[tool] = interface
        return self.available_tools,self.tools_schema
                
    async def execute(self,tool_call:ToolCall)->Tuple[ToolCallStatusCode,Any]:
        """Execute a tool call."""
        logger.typewriter_log(
            "NEXT ACTION: ",
            Fore.CYAN,
            f"TOOL: {Fore.CYAN}{tool_call.tool_name}{Style.RESET_ALL}  \n"
            f"ARGUMENTS: \n{Fore.CYAN}{tool_call.tool_args}{Style.RESET_ALL}",
        )
        
        interface = self.toolif_mapping[tool_call.tool_name]
        status_code,output = interface.execute(tool_call.tool_name,**tool_call.tool_args)
        
        tool_call.data['tool_output'] = output
        tool_call.data['tool_status_code'] = status_code
        
        logger.typewriter_log("Tool Return: ", Fore.CYAN, str(output))
        logger.typewriter_log(
            "TOOL STATUS CODE: ", Fore.CYAN, f"{status_code.color()}{status_code.name}{Style.RESET_ALL}"
        )
        return status_code,output
        
    
    async def step(self,
                   *,
                   force_stop:bool=False,
                   interrupt:bool=False,
                   **kwargs)->ExecutionNode:
        """Step and return execution result."""
        raise NotImplementedError
    
    async def run(self,task:TaskNode,**kwargs)->ExecutionGraph:
        """Execute the engine and return the result node."""
        await self.lazy_init(self.config)
        raise NotImplementedError
        
        
        
        
        