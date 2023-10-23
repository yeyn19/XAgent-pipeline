"""可以自动地执行一个自动机以完成pipeline的功能
"""
from colorama import Fore, Style
from enum import Enum, unique, auto

from XAgent.data_structure.pipeline_automat import PipelineAutoMat, PipelineAutoMatNode
from XAgent.loggers.logs import logger
from XAgent.utils import AutoMatEdgeType

@unique
class AutoMatRunningState(Enum):
    AutoMat = auto()
    ReACT = auto()

class AutoMatRunner():
    """运行一个先验自动机。ReACT的实现视为这里的一个部分
    
    """
    def __init__(self, pipeline: PipelineAutoMat = None):
        self.pipeline = pipeline
        self.state: AutoMatRunningState = AutoMatRunningState.AutoMat
        if self.pipeline == None:
            self.state: AutoMatRunningState = AutoMatRunningState.ReACT

    def find_next_node(self):
        """找到下一个选边。如果找不到，就进行ReACT模式
        """
        pass

    def run(self):
        """传入一个自动机去实际地执行
        1.决定下一个工具是什么
        2.决定下一个工具的输入
        3.执行工具
        4.存储运行时信息
        """
        if self.state == AutoMatRunningState.AutoMat:
            now_node = self.pipeline.nodes[0]
        else:
            now_node = PipelineAutoMatNode.get_duck_node_for_react()
        
        while True:
            #寻找now_node所有的出边
            logger.typewriter_log(
                "Now We are in node",
                Fore.YELLOW,
                now_node.node_name,
            )
            if self.state == AutoMatRunningState.ReACT:
                #ReACT模式
                pass
            else: 
                out_edges = [ edge for edge in self.pipeline.edges if edge.from_node == now_node]
                if len(out_edges) > 0:
                    select, param_piece, selected_edge = False, {}, None
                    for edge in out_edges:
                        if edge.rule_type == AutoMatEdgeType.RuleBased:
                            select, param_piece = edge.route(self.pipeline.runtime_info)
                            if select:
                                selected_edge = edge 
                                break
                    if select: #根据规则选边
                        if selected_edge.given_all_params:
                            # 规则选边、完成所有入参，直接执行该节点
                            edge.param_interface.partly_implement(param_piece)
                            edge.to_node.run(edge.param_interface)
                            exit()
                        else:
                            # todo
                            pass
                else:
                    #没有出边，说明自动机执行完成了
                    pass
                    


