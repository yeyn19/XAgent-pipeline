from colorama import Fore, Style

from XAgent.tools.param_system import ParamSystem
from XAgent.tools.n8n_tools.n8n_compiler import n8n_compiler
from XAgent.loggers.logs import logger


class n8nParamSystem(ParamSystem):
    

    def from_tool_name(self, tool_name):
        """从一个渠道load所有的可能参数
        """
        integration, resource, operation = tool_name.split(".")
        self.n8n_python_node = n8n_compiler.get_n8n_node(
            integration_name=integration,
            resource_name=resource,
            operation_name=operation
        )
        # out = new_node.print_self()
        # if len(new_node.params) > 0:
        #     lines = []
        #     for k, (key, value) in enumerate(new_node.params.items()):
        #         param_des_lines = value.to_description(prefix_ids=f"{k}", indent=0, max_depth=1)
        #         lines.extend(param_des_lines)
        #     print("\n".join(lines))


    def partly_implement(self, given_param_dict):
        """允许用户去部分实现一些参数
        """
        logger.typewriter_log("implement a node for n8n",Fore.BLUE, f"{self.n8n_python_node.node_meta.integration_name}->{self.n8n_python_node.node_meta.resource_name}->{self.n8n_python_node.node_meta.operation_name}")
        print(given_param_dict)
        pass

    

    def to_description(self):
        """向语言模型描述待填写参数
        """
        pass

    def run_tool(self):
        pass