from typing import Any

from XAgent.config import CONFIG

class BaseEngine:
    """The Engine is the core of XAgent, it is responsible to manage the workflow of the XAgent and determine the execution order of the tools."""
    def __init__(self, config=CONFIG):
        self.config = config
        
    def run(self,*args,**kwargs)->Any:
        raise NotImplementedError