# from XAgent.workflow.working_memory import WorkingMemoryAgent
#from XAgent.vector_db import VectorDBInterface
# from XAgent.running_recorder import RunningRecoder
from XAgent.config import CONFIG as __config
from XAgent.agent import agent_dispatcher,PlanGenerateAgent, PlanRefineAgent,ReflectAgent, ToolAgent, RouteAgent

for agent in [PlanGenerateAgent,PlanRefineAgent,ToolAgent,ReflectAgent,RouteAgent]:
    agent_dispatcher.regist_agent(agent)



INTERRUPT = False
INTERRUPT_MESSAGE = None
# working_memory_agent = WorkingMemoryAgent()
# vector_db_interface = VectorDBInterface()
# recorder = RunningRecoder()