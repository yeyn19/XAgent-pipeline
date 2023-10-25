from .base import BaseToolExecutor
from .react import ReActToolExecutor
from .automat import AutomatExecutor


from XAgent.config import CONFIG
reacttoolexecutor = ReActToolExecutor(CONFIG)
automatexecutor = AutomatExecutor(CONFIG)

