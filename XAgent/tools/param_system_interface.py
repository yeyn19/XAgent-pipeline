
from XAgent.tools.param_system import ParamSystem
from XAgent.tools.n8n_tools.n8n_param_system import n8nParamSystem

def get_param_system(tool_name, tool_type) -> ParamSystem:
    if tool_type == "n8n":
        param_system = n8nParamSystem()
        param_system.from_tool_name(tool_name)
        return param_system
    elif tool_type == "intrinsic":
        pass
