from typing import Any,Union,Tuple
from XAgent.utils import Singleton
from XAgent.ai_functions import function_manager
from XAgent.enums import ToolCallStatusCode
from .base import BaseToolInterface

from .customized_tools.example_customize_tools import BaseCustomizeTool, myCalculator


class CustomizedToolInterface(BaseToolInterface):
    """
    这里有个样例的实现
    """
    def __init__(self,*args,**kwargs) -> None:
        pass
        
    def lazy_init(self,config):
        self.tools = [myCalculator()]
        return self
    
    def close(self):
        pass
    
    def get_available_tools(self)->Tuple[list[str],dict]:
        names, all_des = [], []
        for tool in self.tools:
            name, des = tool.function_description()
            names.append(name)
            all_des.append(des)
        return names, all_des
    
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
        for tool in self.tools:
            if tool_name == tool.function_description()[0]:
                return tool.execute(**kwargs)
        assert False, "can't find tool?"
