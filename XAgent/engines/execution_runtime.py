



@dataclass
class RuntimeTool():
    """用来存储工具调用的运行时信息
    """
    tool_output_status_code: ToolCallStatusCode
    output_data: Any

    def log_self(self):
        if self.tool_output_status_code == ToolCallStatusCode.TOOL_CALL_SUCCESS:
            color = Fore.GREEN
        elif self.tool_output_status_code == ToolCallStatusCode.SUBMIT_AS_SUCCESS:
            color = Fore.YELLOW
        elif self.tool_output_status_code == ToolCallStatusCode.SUBMIT_AS_FAILED:
            color = Fore.BLUE
        else:
            color = Fore.RED

        logger.typewriter_log(
            "ToolResult: ", Fore.BLUE, f"{color}{self.output_data}{Style.RESET_ALL}"
        )
        logger.typewriter_log(
            "ToolStatusCode: ", Fore.BLUE, f"{color}{self.tool_output_status_code.name}{Style.RESET_ALL}"
        )


@dataclass
class RuntimeNode():
    """存储单个工具调用的运行时信息以及选边和选参的信息
    """
    call_id: int #第几次被访问
    node_pointer: Optional["PipelineAutoMatNode"] = None #延迟评估
    edge_pointer: Optional["PipelineAutoMatEdge"] = None #延迟评估,选边选参
    tool_call_info: Optional[RuntimeTool] = None


class RuntimeStackUserInterface():
    """暴露给用户来开发Pipeline-rule functions的接口
    1.实现一定要简单易懂
    2.存储运行时的信息
    3.可以设计一些low-code的辅助函数来帮助进行Pipeline设计
    """
    def __init__(self):
        self.runtime_data: List[RuntimeNode] = []
        self.global_data = {}
