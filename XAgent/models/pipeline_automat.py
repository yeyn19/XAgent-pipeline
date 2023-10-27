"""node里存储运行时信息
"""
from __future__ import annotations
from typing import List, Optional, Any, Dict, Callable
from colorama import Fore, Style
from dataclasses import dataclass, field
import importlib
from enum import Enum, auto, unique
import uuid
import types

from XAgent.enums import  ToolCallStatusCode
from XAgent.logs import logger
from XAgent.models.graph import ExecutionGraph, ExecutionNode, DirectedEdge
from XAgent.models.node import ToolCall


@unique
class AutoMatStateChangeHardness(Enum):
    """描述自动机选边的困难程度，用来在运行时选择状态转移消耗的资源"""
    GPT4 = auto()

@unique
class ExecutionNodeTypeForPipelineUserInterface(Enum):
    Start = "Start"
    BuiltIn = 'BuildIn' #Xagent工具
    ToolServer = 'ToolServer'
    Rapid = 'Rapid'
    ToolCombo = "ToolCombo"
    N8N = 'N8N'
    Custom = 'Custom'
    ReACTChain = "ReACT"
    Pipeline = "Pipeline"
    HumanElicitingProcess = "HumanElicit"


@unique
class PipelineRouteType(Enum):
    RuleBasedSelectAndParam = auto()
    AIGiveParam = auto()
    AISelectAndGiveParam = auto()
    def __str__(self):
        return self.name

@dataclass
class PipelineRouteResult():
    select_this_edge: bool
    from_node: "PipelineAutoMatNode"
    to_node: "PipelineAutoMatNode"
    select_edge: "PipelineAutoMatEdge"
    provide_params: dict
    param_sufficient: bool

@dataclass
class PipelineRuntimeNode():
    route_result: PipelineRouteResult
    route_type: PipelineRouteType
    tool_node: ToolCall

@dataclass
class PipelineRuntimeStackUserInterface():
    runtime_stack: List[PipelineRuntimeNode] = field(default_factory=list)
    global_vars: Dict[Any, Any] = field(default_factory=dict)



class PipelineAutoMatNode(ExecutionNode):
    """一个自动机节点"""
    node_name: str
    tool_name: str
    node_type: ExecutionNodeTypeForPipelineUserInterface
    state_change_hardness: AutoMatStateChangeHardness = AutoMatStateChangeHardness.GPT4

    route: Optional[Callable] = None

    """存储该节点在运行时的访问情况"""
    runtime_stack: List[PipelineRuntimeNode] = field(default_factory=list)

    
    @staticmethod
    def from_json(node):
        new_node = PipelineAutoMatNode(
                        node_name=node["node_name"],
                        tool_name=node["tool_name"],
                        node_type=ExecutionNodeTypeForPipelineUserInterface(node["node_type"]),
                    )
        # TODO: other params?
        return new_node

    @staticmethod
    def get_defualt_ReACT_node():
        """对于所有节点默认添加一个ReACT-node作为指向的节点，来处理异常情况
        """
        new_node = PipelineAutoMatNode(
                        node_name="",
                        tool_name="",
                        node_type=ExecutionNodeTypeForPipelineUserInterface.ReACTChain,
                    )
        # TODO: other params?
        return new_node




class PipelineAutoMatEdge(DirectedEdge):
    edge_name: str = ""
    comments: List[str] = field(default_factory=List)

    route: Optional[Callable] = None

    def get_defualt_ReACT_edge():
        new_edge = PipelineAutoMatEdge(
            comments=[
                "the default edge to handle exception: route to this edge when all other conditions didn't happen"
            ]
        )

        return new_edge

    def to_json(self):
        pass



@dataclass
class PipelineMeta():
    name: str
    purpose: str
    author: str
    params: dict
    
    @staticmethod
    def from_json(meta_data):
        return PipelineMeta(
            name=meta_data["name"],
            purpose=meta_data["purpose"],
            author=meta_data["author"],
            params = meta_data["params"]
        )


class PipelineAutoMat(ExecutionGraph):
    """用一个自动机来描述pipeline，是一种动态的RPA方法，每次的选边都由模型来完成。
    同时需要维护一个运行时的调用栈
    """

    meta: PipelineMeta = None
    runtime_info: PipelineRuntimeStackUserInterface = PipelineRuntimeStackUserInterface() #存储自动机的运行时信息



    @staticmethod
    def from_json(json_data: dict, rule_file_name:str):
        automat = PipelineAutoMat(
            meta = PipelineMeta.from_json(json_data["meta"]),
            runtime_info=PipelineRuntimeStackUserInterface(),
        )
        for node in json_data["nodes"]:
            new_node = PipelineAutoMatNode.from_json(node)

            function_name = f"route_node_{new_node.node_name}"
            module = importlib.import_module(rule_file_name)
            # 检查函数是否存在
            if hasattr(module, function_name):
                # 获取函数并将其绑定为实例方法
                func = getattr(module, function_name)
                new_node.route = types.MethodType(func, new_node)
                logger.typewriter_log(f"node \"{new_node.node_name}\"({new_node.tool_name}):",Fore.BLUE, "find existing route-function")
            else:
                logger.typewriter_log(f"node \"{new_node.node_name}\"({new_node.tool_name}):",Fore.BLUE, "use default route-function")

            automat.add_node(new_node)
            if new_node.node_type == ExecutionNodeTypeForPipelineUserInterface.Start:
                automat.begin_node = new_node
            
        for edge in json_data["edges"]:
            new_edge = PipelineAutoMatEdge(
                edge_name=edge["edge_name"],
                comments=edge["comments"],
            )
            from_name = edge["from_node"]
            to_name = edge["to_node"]
            from_node, to_node = None, None
            for node in automat.nodes.values():
                if node.node_name == from_name:
                    from_node = node
                if node.node_name == to_name:
                    to_node = node
            if (not from_node) or (not to_node):
                raise NotImplementedError

            function_name = f"route_edge_{new_edge.edge_name}"
            module = importlib.import_module(rule_file_name)
            # 检查函数是否存在
            if hasattr(module, function_name):
                # 获取函数并将其绑定为实例方法
                func = getattr(module, function_name)
                new_edge.route = types.MethodType(func, new_edge)
                logger.typewriter_log(f"edge \"{new_edge.edge_name}\"({from_node.node_name} -> {to_node.node_name}):",Fore.BLUE, "find existing route-function")
            else:
                logger.typewriter_log(f"edge \"{new_edge.edge_name}\"({from_node.node_name} -> {to_node.node_name}):",Fore.BLUE,  "use default route-function")
        
            automat.add_edge(
                from_node=from_node,
                to_node=to_node,
                edge=new_edge,
            )
        old_nodes = list(automat.nodes.values())
        for node in old_nodes:
            error_handle_node = PipelineAutoMatNode.get_defualt_ReACT_node()
            error_handle_edge = PipelineAutoMatEdge.get_defualt_ReACT_edge()
            error_handle_node.node_name = f"error_handle_node_for_{node.node_name}"
            error_handle_edge.edge_name = f"error_handle_edge_for_{node.node_name}"
            automat.add_node(error_handle_node)
            automat.add_edge(
                from_node=node,
                to_node=error_handle_node,
                edge=error_handle_edge,
            )
        return automat
