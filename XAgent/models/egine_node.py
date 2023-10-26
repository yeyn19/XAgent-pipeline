from XAgent.enums import ToolCallStatusCode,SearchMethodStatusCode

from .node import ToolNode
from .plan import Plan
from .graph import ExecutionGraph,ExecutionNode


class TaskNode(ExecutionNode):
    plan:Plan = None
    begin_node:bool = True

class ToolExecutionNode(ExecutionNode):
    tool_call:ToolNode = None
    status_code:ToolCallStatusCode = ToolCallStatusCode.OTHER_ERROR
    
    
class ReActExecutionGraph(ExecutionGraph):
    status:SearchMethodStatusCode = SearchMethodStatusCode.DOING
    need_for_plan_refine:bool = False