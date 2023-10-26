"""
This module contains the interfaces for the tools. Provide a bridge
between the real world tools with the XAgent.
"""

from .base import BaseToolInterface
from .builtin import BuiltInInterface
from .toolserver import ToolServerInterface
from .rapidapi import RapidAPIInterface