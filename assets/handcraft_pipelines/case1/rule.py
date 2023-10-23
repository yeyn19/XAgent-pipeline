from XAgent.data_structure.pipeline_automat import PipelineAutoMatEdge
from XAgent.data_structure.runtime_user_interface import RuntimeStackUserInterface


def route_1(edge_info: PipelineAutoMatEdge,runtime_stack: RuntimeStackUserInterface) -> (bool, dict):
    """给边1写规则。返回是否选边，以及传参
    """
    print(f"dynamically running user provided function\"route_1\"")
    return True, {"message":"hello world"}