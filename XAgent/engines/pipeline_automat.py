"""pipeline-automat的执行和选边逻辑
"""

from typing import Any
from XAgent.config import CONFIG
from XAgent.data_structure import ToolNode

from .base import BaseEngine

class AutomatExecutor(BaseEngine):
    def __init__(self, config=CONFIG):
        super().__init__(config)

    