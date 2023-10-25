from enum import Enum, unique

from XAgent.tools.n8n_tools.n8n_params import *
from XAgent.tools.n8n_tools.n8n_node import n8nPythonNode


def parse_display_options(display_options, node: n8nPythonNode) -> bool:
    # TODO: implement "hide", implement others
    if "show" in display_options.keys():
        if "resource" in display_options["show"]:
            if node.node_meta.resource_name not in display_options["show"]["resource"]:
                return False
        if "operation" in display_options["show"]:
            if node.node_meta.operation_name not in display_options["show"]["operation"]:
                return False
    else:
        return False
    return True

def parse_properties(node: n8nPythonNode):
    """对于一个特定的函数，假如已经设定好了 integration, resource, operation, 以及部分params的情况下。告诉模型下面需要输入的参数是什么
    """
    node_json = node.node_json
    parameter_descriptions = {}

    for content in node_json["properties"]:
        assert type(content) == dict
        parameter_name = content["name"]

        if parameter_name in ["resource", "operation", "authentication"]:
            continue
        
        if "displayOptions" in content.keys() and (parse_display_options(content["displayOptions"], node) == False):
            continue

        parameter_type = content["type"]

        new_param = visit_parameter(content)
        if new_param != None:
            parameter_descriptions[parameter_name] = new_param
    return parameter_descriptions