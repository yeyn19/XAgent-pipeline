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

class ExecutionType(Enum):
    AtomicTool = auto()
    ReACTChain = auto()
    AutoMatProcess = auto()
    HumanElicitingProcess = auto()



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
    MODIFY_SUCCESS = 0
    MODIFY_FORMER_PLAN = 1
    PLAN_OPERATION_NOT_FOUND = 2
    TARGET_SUBTASK_NOT_FOUND = 3
    PLAN_REFINE_EXIT = 4
    OTHER_ERROR = 5

@unique
class SearchMethodStatusCode(Enum):
    DOING = 0
    SUCCESS = 1
    FAIL = 2
    HAVE_AT_LEAST_ONE_ANSWER = 3 

@unique
class TaskStatusCode(Enum):
    TODO = 0
    DOING = 1
    SUCCESS = 2
    FAIL = 3
    SPLIT = 4 


@unique
class AutoMatStateChangeHardness(Enum):
    """描述自动机选边的困难程度，用来在运行时选择状态转移消耗的资源"""
    GPT4 = auto()

@unique
class RequiredAbilities(Enum):
    tool_tree_search = 0
    plan_generation = 1
    plan_refinement = 2
    task_evaluator = 3
    summarization = 4
    reflection = 5