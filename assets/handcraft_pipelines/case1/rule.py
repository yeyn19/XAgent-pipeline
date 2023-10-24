from XAgent.data_structure.pipeline_automat import PipelineAutoMatEdge, RouteResult, RuntimeStackUserInterface


def route_edge_1(edge_info: PipelineAutoMatEdge,pipeline_param: dict, runtime_stack: RuntimeStackUserInterface) -> RouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    print(f"dynamically running user provided function\"route_1\"")
    params = {
        "select": "channel",
        "channelId": {
            "value": "#general",
            "mode": "name"
        },
        "text": "hello world, I am XAgent-pipeline",
        "otherOptions": {}
    }
    return RouteResult(
        select_node=edge_info.to_node,
        select_edge=edge_info,
        params=params,
        param_sufficient=True,
    )

def route_edge_2(edge_info: PipelineAutoMatEdge, pipeline_param: dict, runtime_stack: RuntimeStackUserInterface) -> RouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    print(f"dynamically running user provided function\"route_2\"")
    params = {
    }
    return RouteResult(
        select_node=edge_info.to_node,
        select_edge=edge_info,
        params=params,
        param_sufficient=True,
    )