import os
from copy import deepcopy
import abc
from typing import List
from dataclasses import dataclass

from XAgent.message_history import MessageHistory
from XAgent.utils import ToolCallStatusCode, TaskStatusCode



class Node(metaclass = abc.ABCMeta):
    def __init__(self):
        pass

@dataclass
class ToolNode(Node):
    def __init__(self):

        self.data = {
            "content": "",
            "thoughts": {
                "properties": {
                    "thought": "",
                    "reasoning": "",
                    "plan": "",
                    "criticism": "",
                },
            },
            "command": {
                "properties": {
                    "name": "",
                    "args": "",
                },
            },
            "tool_output": "",
            "tool_status_code": ToolCallStatusCode.TOOL_CALL_SUCCESS,
        }


    def to_json(self):
        data = deepcopy(self.data)
        data["tool_status_code"] = data["tool_status_code"].name
        return data




