
from abc import ABC, abstractmethod
from typing import Any

from XAgent.enums import ToolCallStatusCode

class BaseCustomizeTool(ABC):
    """这里怎么实现都行，可以不是python，但是必须提供一个OpenAI-function-json和一个execute接口"""
    @abstractmethod
    def function_description(self) -> (str, dict):
        pass

    @abstractmethod
    def execute(self, params) -> [ToolCallStatusCode, Any]:
        pass



class myCalculator(BaseCustomizeTool):
    """这只是一个例子"""
    def function_description(self) -> (str, dict):
        name = "calculator"
        description = {
            "name": name,
            "description": "doing base math expressions",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string"
                    }
                },
                "required": ["expression"],
            }
        }
        return name, description


    def execute(self, **params) -> [ToolCallStatusCode, Any]:
        try:
            output = eval(params["expression"])
            return ToolCallStatusCode.TOOL_CALL_SUCCESS, {"result":output}
        except:
            return ToolCallStatusCode.OTHER_ERROR, {}