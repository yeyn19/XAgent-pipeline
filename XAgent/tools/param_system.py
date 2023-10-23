"""管理所有工具的参数
1.方便用户去快速填写相关参数
2.方便语言模型去填写剩余的参数
3.把所有工具都对齐到这套标准
"""
from abc import ABC, abstractmethod

from XAgent.utils import ToolCallStatusCode


class ParamSystem(ABC):


    @abstractmethod
    def partly_implement(self, given_param_dict):
        """允许用户去部分实现一些参数
        """
        pass

    
    @abstractmethod
    def to_description(self):
        """向语言模型描述待填写参数
        """
        pass

    @abstractmethod
    def run_tool(self):
        pass

