"""node里存储运行时信息
"""
from __future__ import annotations
from typing import List, Optional
from colorama import Fore, Style
from dataclasses import dataclass, field
import importlib
import uuid
import types

from XAgent.utils import AutoMatEdgeType, AutoMatStateChangeHardness
from XAgent.tools.param_system import ParamSystem
from XAgent.tools.param_system_interface import get_param_system
from XAgent.loggers.logs import logger
from XAgent.data_structure.runtime_user_interface import RuntimeStackUserInterface


@dataclass
class RuntimeTool():
    """用来存储工具调用的运行时信息
    """

@dataclass
class RuntimeNode():
    """存储单个工具调用的运行时信息以及选边和选参的信息
    """
    call_id: int #第几次被访问
    node_pointer: Optional["PipelineAutoMatNode"] = None #延迟评估
    edge_pointer: Optional["PipelineAutoMatEdge"] = None #延迟评估,选边选参
    tool_call_info: Optional[RuntimeTool] = None


@dataclass
class RuntimeChain():
    """数据类，存储原始的工具调用链
    和Pipeline运行交互
    """
    tool_call_stack: List[RuntimeNode] = field(default_factory=list)




@dataclass
class PipelineAutoMatNode():
    """一个自动机节点"""
    node_name: str
    tool_name: str
    tool_type: str
    state_change_hardness: AutoMatStateChangeHardness = AutoMatStateChangeHardness.GPT4

    """存储该节点在运行时的访问情况"""
    runtime_stack: List = field(default_factory=list)
    
    @staticmethod
    def from_json(node):
        new_node = PipelineAutoMatNode(
                        node_name=node["node_name"],
                        tool_name=node["tool_name"],
                        tool_type=node["tool_type"],
                    )
        # TODO: other params?
        return new_node

    @staticmethod
    def get_duck_node_for_react():
        new_node = PipelineAutoMatNode(
                        node_name=uuid.uuid1(),
                        tool_name=node["tool_name"],
                        tool_type=node["tool_type"],
                    )
        # TODO: other params?
        return new_node

    def run(self, param_system: ParamSystem):
        """进行工具调用
        """
        pass


@dataclass
class PipelineAutoMatEdge():
    edge_name: str
    from_node: Optional[PipelineAutoMatNode] = None
    to_node: Optional[PipelineAutoMatNode] = None

    param_interface: Optional[ParamSystem] = None

    rule_type: AutoMatEdgeType = AutoMatEdgeType.NaturalLanguageBased
    given_all_params: bool = False
    nl_suggesstions: List[str] = field(default_factory=List)

    def route(self, runtime_stack: RuntimeStackUserInterface):
        """选边函数，根据规则来选边：可能是一个user-provided rule，也可以是LLM根据建议自动选边
        这个函数的实现是从pipeline/rule.py中动态加载的
        """
        print("User to be implemented")
        raise NotImplementedError

    def to_json(self):
        pass



@dataclass
class PipelineMeta():
    name: str
    purpose: str
    author: str
    
    @staticmethod
    def from_json(meta_data):
        return PipelineMeta(
            name=meta_data["name"],
            purpose=meta_data["purpose"],
            author=meta_data["author"],
        )

class PipelineAutoMat():
    """用一个自动机来描述pipeline，是一种动态的RPA方法，每次的选边都由模型来完成。
    同时需要维护一个运行时的调用栈
    
    """
    def __init__(self):
        self.nodes: List[PipelineAutoMatNode] = []
        self.edges: List[PipelineAutoMatEdge] = []
        self.runtime_info: RuntimeChain = None #存储自动机的运行时信息

        self.meta: PipelineMeta = None


    @staticmethod
    def from_json(json_data: dict, rule_file_name:str):
        automat = PipelineAutoMat()
        automat.meta = PipelineMeta.from_json(json_data["meta"])
        for node in json_data["nodes"]:
            automat.nodes.append(PipelineAutoMatNode.from_json(node))
        for edge in json_data["edges"]:
            edge_data = PipelineAutoMatEdge(
                edge_name=edge["edge_name"],
                nl_suggesstions=edge["nl_suggestions"],
            )
            if edge["rule_based_select"]:
                edge_data.rule_type = AutoMatEdgeType.RuleBased
                #加载实际的对象
                function_name = f"route_{edge_data.edge_name}"
                logger.info(f"go to find {function_name}")
                module = importlib.import_module(rule_file_name)
                # 检查函数是否存在
                if hasattr(module, function_name):
                    # 获取函数并将其绑定为实例方法
                    func = getattr(module, function_name)
                    edge_data.route = types.MethodType(func, edge_data)
                else:
                    raise ValueError(f"Function {function_name} does not exist in {rule_file_name}.py")
            else:
                edge_data.rule_type = AutoMatEdgeType.NaturalLanguageBased

            edge_data.given_all_params = edge["given_all_params"]
            

            from_name = edge["from_node"]
            to_name = edge["to_node"]
            for node in automat.nodes:
                if node.node_name == from_name:
                    edge_data.from_node = node
                if node.node_name == to_name:
                    edge_data.to_node = node
            if edge_data.from_node == None or edge_data.to_node == None:
                raise NotImplementedError

            edge_data.param_interface = get_param_system(edge_data.to_node.tool_name, edge_data.to_node.tool_type)
            
            automat.edges.append(edge_data)
        return automat
