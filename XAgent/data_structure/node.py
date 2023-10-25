import os
import abc
from copy import deepcopy
from enum import Enum
from typing import List
from dataclasses import dataclass

from XAgent.message_history import MessageHistory
from XAgent.utils import ToolCallStatusCode, TaskStatusCode,ToolType



class Node(metaclass = abc.ABCMeta):
    def __init__(self):
        pass
        

class ToolNode(Node):
    """存储所有工具相关信息的数据结构
    """
    def __init__(self,data:dict = None,tool_type=ToolType.Default):
        self.tool_type = tool_type
        self.father: ToolNode = None

        self.expand_num = 0
        if data is not None:
            self.data = data 
        else:
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

    def set_tool(self,tool_name,tool_args):
        self.data["command"]["properties"]["name"] = tool_name
        self.data["command"]["properties"]["args"] = tool_args

    def to_json(self):
        data = deepcopy(self.data)
        data["tool_status_code"] = data["tool_status_code"].name
        return data




