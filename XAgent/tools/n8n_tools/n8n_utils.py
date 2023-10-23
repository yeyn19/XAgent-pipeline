from enum import Enum, unique, auto
from dataclasses import dataclass


@unique
class n8nParamParseStatus(Enum):
    #params识别问题
    ParamParseSuccess = auto()
    UndefinedParam = auto() # 未定义的参数
    ParamTypeError = auto() # 输入格式错误
    UnSupportedParam = auto() #不应该提供这个参数
    UnsupportedExpression = auto() #这个字段不能含参数
    ExpressionError = auto() #表达式不合理
    RequiredParamUnprovided = auto() #未提供require field

@unique
class NodeType(Enum):
    action = auto()
    trigger = auto()


@dataclass
class n8nNodeMeta():
    node_type: NodeType = NodeType.action
    integration_name: str = ""
    resource_name: str = ""
    operation_name: str = ""
    operation_description: str = ""

    def to_action_string(self):
        output = f"{self.node_type.name}(resource={self.resource_name}, operation={self.operation_name})"
        if self.operation_description != "":
            output += f": {self.operation_description}"
        return output