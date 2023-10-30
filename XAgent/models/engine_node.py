from dataclasses import field

from XAgent.enums import ToolCallStatusCode,TaskStatusCode

from .node import ToolCall
from .plan import Plan
from .graph import ExecutionGraph,ExecutionNode,TaskNode



class ReActExecutionNode(ExecutionNode):
    status_code:ToolCallStatusCode = ToolCallStatusCode.OTHER_ERROR
    
class ReActExecutionGraph(ExecutionGraph):
    need_for_plan_refine:bool = False
    
class PlanExecutionNode(TaskNode):
    role:str = None
    task:str = None
    actions:list[ToolCall] = None
    status_code: TaskStatusCode = TaskStatusCode.TODO

class PipelineTaskNode(TaskNode):
    pipeline_dir: str = None
    overall_task_description: str = None
    pipeline_input_params: dict = field(default_factory=dict)
    
class PlanExecutionGraph(ExecutionGraph):
    pass