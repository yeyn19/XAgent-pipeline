# from XAgent.workflow.working_memory import WorkingMemoryAgent
from XAgent.agent.dispatcher import agent_dispatcher
#from XAgent.vector_db import VectorDBInterface
# from XAgent.running_recorder import RunningRecoder
from XAgent.config import CONFIG as __config
from XAgent.tools import ReActToolExecutor, ToolServerInterface

global_tool_server_interface = ToolServerInterface()
reacttoolexecutor = ReActToolExecutor(__config)
INTERRUPT = False
INTERRUPT_MESSAGE = None
# working_memory_agent = WorkingMemoryAgent()
# vector_db_interface = VectorDBInterface()
# recorder = RunningRecoder()