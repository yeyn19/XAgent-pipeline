# -*- coding: utf-8 -*-
# This package is used to define the interface between XAgent engines and the tool services
# like ToolServer, BuildIn tools, RapidAPI tools, etc.
# The ToolExecutor is responsible to execute the tools and manage multiple tool interfaces.

from .executor import BaseToolExecutor,ReActToolExecutor
from .interfaces import BaseToolInterface,ToolServerInterface,BuiltInInterface