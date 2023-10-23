from dataclasses import dataclass, field
from typing import List





class RuntimeStackUserInterface():
    """暴露给用户来开发Pipeline-rule functions的接口
    1.实现一定要简单易懂
    2.存储运行时的信息
    3.可以设计一些low-code的辅助函数来帮助进行Pipeline设计
    """
    def __init__(self):
        self.runtime_data: RuntimeChain = []
