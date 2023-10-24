from colorama import Fore, Style

from XAgent.tools.param_system import ParamSystem
from XAgent.tools.n8n_tools.n8n_param_system import n8nParamSystem
from XAgent.loggers.logs import logger
from XAgent.utils import ToolType

def get_param_system(tool_name, tool_type) -> ParamSystem:
    if tool_type == ToolType.n8nTool:
        param_system = n8nParamSystem()
        param_system.from_tool_name(tool_name)
        return param_system
    else:
        logger.typewriter_log(f"{tool_type.value}:{tool_name} Not Implement param_system", Fore.BLUE)
