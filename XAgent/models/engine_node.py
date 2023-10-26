from XAgent.enums import ToolCallStatusCode,EngineExecutionStatusCode

from .node import ToolNode
from .plan import Plan
from .graph import ExecutionGraph,ExecutionNode



class ReActExecutionNode(ExecutionNode):
    tool_call:ToolNode = None
    status_code:ToolCallStatusCode = ToolCallStatusCode.OTHER_ERROR
    
    
class ReActExecutionGraph(ExecutionGraph):
    status:EngineExecutionStatusCode = EngineExecutionStatusCode.DOING
    need_for_plan_refine:bool = False