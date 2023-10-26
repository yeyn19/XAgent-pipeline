from XAgent.models.pipeline_automat import PipelineAutoMat, PipelineAutoMatEdge, PipelineRouteResult,  PipelineRuntimeStackUserInterface

# params = {
#     "select": "channel",
#     "channelId": {
#         "value": "#general",
#         "mode": "name"
#     },
#     "text": "hello world, I am XAgent-pipeline",
#     "otherOptions": {}
# }
def route_edge_1(edge_info: PipelineAutoMatEdge, pipeline: PipelineAutoMat, runtime_stack: PipelineRuntimeStackUserInterface) -> PipelineRouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    print(f"dynamically running user provided function\"route_1\"")
    params = {
        "expression": "1+2+3*5"
    }
    from_node, to_node = pipeline.get_edge_nodes(edge_info)
    return PipelineRouteResult(
        select_this_edge=True,
        from_node=from_node,
        to_node=to_node,
        select_edge=edge_info,
        provide_params=params,
        param_sufficient=True,
    )

def route_edge_2(edge_info: PipelineAutoMatEdge, pipeline: PipelineAutoMat, runtime_stack: PipelineRuntimeStackUserInterface) -> PipelineRouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    print(f"dynamically running user provided function\"route_2\"")
    params = {
    }
    from_node, to_node = pipeline.get_edge_nodes(edge_info)
    return PipelineRouteResult(
        select_this_edge=True,
        from_node=from_node,
        to_node=to_node,
        select_edge=edge_info,
        provide_params=params,
        param_sufficient=True,
    )

def route_edge_3(edge_info: PipelineAutoMatEdge, pipeline: PipelineAutoMat, runtime_stack: PipelineRuntimeStackUserInterface) -> PipelineRouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    params = {
        "filepath":"./a.txt",
        "content": "nmsl",
    }
    from_node, to_node = pipeline.get_edge_nodes(edge_info)
    return PipelineRouteResult(
        select_this_edge=True,
        from_node=from_node,
        to_node=to_node,
        select_edge=edge_info,
        provide_params=params,
        param_sufficient=True,
    )

def route_edge_4(edge_info: PipelineAutoMatEdge, pipeline: PipelineAutoMat, runtime_stack: PipelineRuntimeStackUserInterface) -> PipelineRouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    params = {}
    from_node, to_node = pipeline.get_edge_nodes(edge_info)
    return PipelineRouteResult(
        select_this_edge=True,
        from_node=from_node,
        to_node=to_node,
        select_edge=edge_info,
        provide_params=params,
        param_sufficient=True,
    )

def route_edge_5(edge_info: PipelineAutoMatEdge, pipeline: PipelineAutoMat, runtime_stack: PipelineRuntimeStackUserInterface) -> PipelineRouteResult:
    """给边1写规则。返回是否选边，以及传参
    """
    params = {
        "query": "(1+1)^100=?"
    }
    from_node, to_node = pipeline.get_edge_nodes(edge_info)
    return PipelineRouteResult(
        select_this_edge=True,
        from_node=from_node,
        to_node=to_node,
        select_edge=edge_info,
        provide_params=params,
        param_sufficient=True,
    )