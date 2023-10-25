"""可以自动地执行一个自动机以完成pipeline的功能
"""
from colorama import Fore, Style
from enum import Enum, unique, auto


from XAgent.data_structure.pipeline_automat import PipelineAutoMat, PipelineAutoMatNode, RouteResult, RuntimeStackUserInterface, RuntimeTool, RuntimeNode
from XAgent.logs import logger
from XAgent.utils import has_route_function, AutoMatEdgeType
from XAgent.tools.param_system import ParamSystem

                
def default_route_node(now_node: PipelineAutoMatNode, pipeline_param: dict, runtime_stack: RuntimeStackUserInterface):
    """再该执行完以后，决定下一个node是什么，做route等事情
    """
    for out_edge in now_node.out_edges:

        if has_route_function(out_edge):
            route_result: RouteResult = out_edge.route(pipeline_param, runtime_stack)
            # import pdb; pdb.set_trace()
            if route_result.select_node != None:
                return route_result

def ai_route_function(now_node: PipelineAutoMatNode, pipeline_param: dict, runtime_stack: RuntimeStackUserInterface, target_node: PipelineAutoMatNode = None):
    raise NotImplementedError



def run_pipeline(pipeline: PipelineAutoMat):
    visit_count = 0
    now_node = pipeline.start_node #start_node不需要执行，直接route
    while True:
        if len(now_node.out_edges) == 1 and (now_node.out_edges[0].edge_name.startswith("exception_edge_for") ): 
            logger.typewriter_log(
                "pipeline running to the end",
                Fore.YELLOW
            )
            break
        route_result: RouteResult = None
        if has_route_function(now_node):
            user_route_result: RouteResult = now_node.route(pipeline.meta.params, pipeline.runtime_info)
            if user_route_result.select_node != None:
                route_result = user_route_result
        else:
            default_route_result = default_route_node(now_node, pipeline.meta.params, pipeline.runtime_info)
            if default_route_result.select_node != None:
                route_result = default_route_result
        
        if not route_result:
            route_result = ai_route_function(now_node, pipeline.meta.params, pipeline.runtime_info)
        assert route_result != None

        next_node = route_result.select_node
        logger.typewriter_log(
            f"pipeline newly select node \"{next_node.node_name}\"",
            Fore.YELLOW,
            f"{next_node.tool_type}: {next_node.tool_name}"
        )

        next_node.param_interface.partly_implement(given_param_dict=route_result.params)
        if route_result.param_sufficient and (not next_node.param_interface.param_sufficient):
            logger.typewriter_log(
                f"assert params for {next_node.node_name} is sufficient, but is not",
                Fore.RED
            )
            exit()

        if not route_result.param_sufficient:
            route_result = ai_route_function(now_node, pipeline.meta.params, pipeline.runtime_info, target_node=next_node)
            next_node.param_interface.partly_implement(given_param_dict=route_result.params)
        assert route_result.param_sufficient

        output, status_code = next_node.param_interface.run_tool()
        runtime_node = RuntimeNode(
                                call_id=visit_count,
                                node_pointer=next_node,
                                edge_pointer=route_result.select_edge,
                                tool_call_info=RuntimeTool(
                                                tool_output_status_code=status_code,
                                                output_data=output
                                            )
                                )
        runtime_node.tool_call_info.log_self()
        pipeline.runtime_info.runtime_data.append(runtime_node)
        next_node.runtime_stack.append(runtime_node)
    
        now_node = next_node
        visit_count += 1