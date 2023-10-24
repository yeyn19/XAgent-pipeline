from XAgent.data_structure.pipeline_automat import PipelineAutoMatEdge, RouteResult
from XAgent.data_structure.runtime_user_interface import RuntimeStackUserInterface


def route_edge_1(edge_info: PipelineAutoMatEdge,pipeline_param: dict, runtime_stack: RuntimeStackUserInterface) -> RouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    print(f"dynamically running user provided function\"route_1\"")
    return RouteResult(
        select_node=edge_info.to_node,
        params={"message":"hello world"},
        param_sufficient=True,
    )