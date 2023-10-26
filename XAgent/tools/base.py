from typing import Any,Union,Tuple
from XAgent.utils import Singleton
from XAgent.ai_functions import function_manager
from XAgent.enums import ToolCallStatusCode


class BaseToolInterface(metaclass=Singleton):
    """
    ToolInterface is used to interact with the tools, including retrieving the 
    tools, executing the tools and getting the schema of the tools.
    Interface is the bridge between the XAgent and tool services.
    """
    def __init__(self,*args,**kwargs) -> None:
        pass
        
    def lazy_init(self,config):
        return self
    
    def close(self):
        pass
    
    def get_available_tools(self)->Tuple[list[str],dict]:
        pass
    
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
        pass