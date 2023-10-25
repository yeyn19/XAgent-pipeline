from typing import Any
from XAgent.config import CONFIG
from XAgent.data_structure import ToolNode
from XAgent.utils import ToolType

from .base import BaseToolExecutor
from ..interfaces import BuiltInInterface, ToolServerInterface


class ReActToolExecutor(BaseToolExecutor):
    """ReActToolExecutor is the default ToolExecutor for ReAct. It is responsible to execute the tools and manage the tool interfaces related to react."""
    def __init__(self, config=CONFIG):
        super().__init__(config)

    
    def lazy_init(self, config=CONFIG):
        super().lazy_init(config)
        self.set_interface_for_type(
            ToolType.BuiltIn, BuiltInInterface().lazy_init(config))
        self.set_interface_for_type(
            ToolType.ToolServer, ToolServerInterface().lazy_init(config))