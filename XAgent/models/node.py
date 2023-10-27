import os
import abc
from copy import deepcopy
from pydantic import BaseModel
from enum import Enum
from typing import List
from dataclasses import dataclass, field

from XAgent.message_history import MessageHistory
from XAgent.enums import ToolCallStatusCode, TaskStatusCode,ToolType



class Node(metaclass = abc.ABCMeta):
    def __init__(self):
        pass
        


class ToolCall(BaseModel):
    """存储所有工具相关信息的数据结构
    """
    tool_type: ToolType = ToolType.Default
    father: 'ToolCall' = None
    expand_num: int = 0
    data: dict = field(default_factory=lambda: {
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
    })


    @property
    def content(self):
        return self.data["content"]
    
    @property
    def thought(self):
        if self.data["thoughts"]["properties"].get('thought','') == "":
            return None
        return self.data["thoughts"]["properties"]["thought"]
    
    @property
    def reasoning(self):
        if self.data["thoughts"]["properties"].get('reasoning','') == "":
            return None
        return self.data["thoughts"]["properties"]["reasoning"]
    
    @property
    def plan(self):
        if self.data["thoughts"]["properties"].get('plan','')== "":
            return None
        return self.data["thoughts"]["properties"]["plan"]
    
    @property
    def criticism(self):
        if self.data["thoughts"]["properties"].get("criticism",'') == "":
            return None
        return self.data["thoughts"]["properties"]["criticism"]
    
    @property
    def tool_name(self):
        if self.data["command"]["properties"]["name"] == "":
            return None
        return self.data["command"]["properties"]["name"]
    @property
    def tool_args(self):
        if self.data["command"]["properties"]["args"] == "":
            return None
        return self.data["command"]["properties"]["args"]

    @property
    def tool_output(self):
        if self.data["tool_output"] == "":
            return None
        return self.data["tool_output"]
    @property
    def status(self):
        return self.data["tool_status_code"]

    def set_tool(self,tool_name,tool_args):
        self.data["command"]["properties"]["name"] = tool_name
        self.data["command"]["properties"]["args"] = tool_args

    def to_json(self):
        data = deepcopy(self.data)
        data["tool_status_code"] = data["tool_status_code"].name
        return data
