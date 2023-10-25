from typing import Any
from XAgent.config import CONFIG
from XAgent.data_structure import ToolNode,ToolType

from .base import BaseToolExecutor
from XAgent.tool_interface import BuiltInInterface, ToolServerInterface


class ReActToolExecutor(BaseToolExecutor):
    def __init__(self, config=CONFIG):
        super().__init__(config)

    
    def lazy_init(self, config=CONFIG):
        super().lazy_init(config)
        self.set_interface_for_type(
            ToolType.BuiltIn, BuiltInInterface().lazy_init(config))
        self.set_interface_for_type(
            ToolType.ToolServer, ToolServerInterface().lazy_init(config))

    def execute(self,tool_node:ToolNode)->Tuple[ToolCallStatusCode,Any]:
        """react执行代码迁移到这里？"""
        pass