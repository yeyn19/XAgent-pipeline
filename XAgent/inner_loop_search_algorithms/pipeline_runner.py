"""可以自动地执行一个自动机以完成pipeline的功能
"""
from colorama import Fore, Style
from enum import Enum, unique, auto


from XAgent.data_structure.pipeline_automat import PipelineAutoMat, PipelineAutoMatNode, RouteResult
from XAgent.data_structure.runtime_user_interface import RuntimeStackUserInterface
from XAgent.loggers.logs import logger
from XAgent.utils import has_route_function, AutoMatEdgeType, ToolType
from XAgent.tools.param_system import ParamSystem

                
def default_route_node(now_node: PipelineAutoMatNode, pipeline_param: dict, runtime_stack: RuntimeStackUserInterface):
    """再该执行完以后，决定下一个node是什么，做route等事情
    """
    for out_edge in now_node.out_edges:
        if has_route_function(out_edge):
            route_result: RouteResult = out_edge.route(pipeline_param, runtime_stack)
            if route_result.select != None:
                return route_result

def ai_route_function(now_node: PipelineAutoMatNode, pipeline_param: dict, runtime_stack: RuntimeStackUserInterface):
    raise NotImplementedError

def run_node(now_node: PipelineAutoMatNode):
    """做route等一系列事情
    1.执行工具
    2.存储运行时信息
    """
    pass

def run_pipeline(pipeline: PipelineAutoMat):
    now_node = pipeline.start_node #start_node不需要执行，直接route
    while True:
        if len(now_node.out_edges) == 0:
            logger.typewriter_log(
                "pipeline running to the end",
                Fore.YELLOW
            )
            break
        route_result: RouteResult = None
        if has_route_function(now_node):
            user_route_result: RouteResult = now_node.route(pipeline.param, pipeline.runtime_info)
            if user_route_result.select_node != None:
                route_result = user_route_result
        else:
            default_route_result = default_route_node(now_node, pipeline_param, pipeline.runtime_info)
            if user_route_result.select_node != None:
                route_result = user_route_result
        
        if not route_result:
            route_result = ai_route_function(now_node, pipeline.param, pipeline.runtime_info)
        assert route_result != None

        next_node = route_result.select_node

        next_node.param_interface.partly_implement(given_param_dict=route_result.params)
        if route_result.param_sufficient and (not next_node.param_interface.param_sufficient):
            logger.typewriter_log(
                f"assert params for {next_node.node_name} is sufficient, but is not",
                Fore.RED
            )
            exit()

        if route_result.param_sufficient:
            output = run_node(next_node)
        