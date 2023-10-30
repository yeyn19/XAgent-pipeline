from enum import Enum, unique, auto
from colorama import Fore, Style

@unique
class LLMStatusCode(Enum):
    SUCCESS = 0
    ERROR = 1

#Tool的设计要保证原子性
class ToolType(Enum): 
    Default = 'Default'
    BuiltIn = 'BuildIn' #Xagent工具
    ToolServer = 'ToolServer'
    Rapid = 'Rapid'
    ToolCombo = "ToolCombo"
    N8N = 'N8N'
    Custom = 'Custom'
    def __hash__(self):
        return hash(self.value)



@unique
class ToolCallStatusCode(Enum):
    TOOL_CALL_FAILED = -1
    TOOL_CALL_SUCCESS = 0
    FORMAT_ERROR = 1
    HALLUCINATE_NAME = 2 
    OTHER_ERROR = 3 
    TIMEOUT_ERROR = 4
    TIME_LIMIT_EXCEEDED = 5
    SERVER_ERROR = 6
    
    SUBMIT_AS_SUCCESS = 7
    SUBMIT_AS_FAILED = 8
    def __str__(self):
        return self.__class__.__name__ + ": " + self.name
    def color(self):
        match self.name:
            case "TOOL_CALL_SUCCESS":
                return Fore.GREEN
            case "SUBMIT_AS_SUCCESS":
                return Fore.GREEN
            case "SUBMIT_AS_FAILED":
                return Fore.BLUE
            case _:
                return Fore.RED
@unique
class PlanOperationStatusCode(Enum):
    MODIFY_SUCCESS = 'MODIFY_SUCCESS'
    MODIFY_FORMER_PLAN = 'MODIFY_FORMER_PLAN'
    PLAN_OPERATION_NOT_FOUND = 'PLAN_OPERATION_NOT_FOUND'
    TARGET_SUBTASK_NOT_FOUND = 'TARGET_SUBTASK_NOT_FOUND'
    PLAN_REFINE_EXIT = 'PLAN_REFINE_EXIT'
    OTHER_ERROR = 'OTHER_ERROR'
    def color(self):
        match self.name:
            case "MODIFY_SUCCESS":
                return Fore.GREEN
            case "MODIFY_FORMER_PLAN":
                return Fore.RED
            case "PLAN_OPERATION_NOT_FOUND":
                return Fore.RED
            case "TARGET_SUBTASK_NOT_FOUND":
                return Fore.RED
            case "PLAN_REFINE_EXIT":
                return Fore.BLUE
            case _:
                return Fore.RED
    
@unique
class EngineExecutionStatusCode(Enum):
    DOING = 'DOING'
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'
    HAVE_AT_LEAST_ONE_ANSWER = 'HAVE_AT_LEAST_ONE_ANSWER'

@unique
class TaskStatusCode(Enum):
    TODO = 'TODO'
    DOING = 'DOING'
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'
    SPLIT = 'SPLIT'
    
    def color(self):
        match self.name:
            case "SUCCESS":
                return Fore.GREEN
            case "FAIL":
                return Fore.RED
            case "DOING":
                return Fore.BLUE
            case "SPLIT":
                return Fore.YELLOW
            case _:
                return Fore.WHITE

@unique
class RequiredAbilities(Enum):
    tool_tree_search = 'tool_tree_search'
    plan_generation = 'plan_generation'
    plan_refinement = 'plan_refinement'
    task_evaluator = 'task_evaluator'
    summarization = 'summarization'
    reflection = 'reflection'
    route_pipeline = "route_pipeline"