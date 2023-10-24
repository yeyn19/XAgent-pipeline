from typing import List, Dict
from dataclasses import dataclass, field
from enum import Enum, unique
from copy import deepcopy
import json

from XAgent.tools.n8n_tools.n8n_utils import n8nNodeMeta, n8nParamParseStatus, NodeType
from XAgent.tools.n8n_tools.n8n_params import n8nParameter


@dataclass
class n8nPythonNode():
    """将n8n node转化为一个python-function
    """
    node_meta: n8nNodeMeta = field(default_factory=n8nNodeMeta())
    node_json: dict = field(default_factory=lambda: {})
    params: Dict[str, n8nParameter] = field(default_factory=lambda: {})

    implemented: bool = False
    

    def get_name(self):
        return f"{self.node_meta.node_type.name}"


    def update_implement_info(self):
        if len(self.params) == 0:
            self.implemented = True
            return
        for key, value in self.params.items():
            if value.data_is_set:
                self.implemented = True
                return

    def print_self(self):
        """返回一个多行文本
        """
        lines = []
        input_data = "input_data: List[Dict] =  [{...}]" if self.node_meta.node_type == NodeType.action else ""
        define_line = f"def {self.get_name()}({input_data}):"
        lines.append(define_line)
        
        
        param_json = {}
        for key, value in self.params.items():
            param = value.to_json()
            if param != None:
                param_json[key] = param


        param_str = json.dumps(param_json, indent = 2, ensure_ascii=False)
        param_str = param_str.splitlines(True)
        param_str = [line.strip("\n") for line in param_str]
        prefix = "  params = "
        param_str[0] = prefix + param_str[0]
        if not self.implemented:
            if len(self.params) > 0:
                param_str[0] += "  # to be Implemented"
            else:
                param_str[0] += "  # This function doesn't need spesific param"
        for i in range(1, len(param_str)):
            param_str[i] = " "*len(prefix) + param_str[i]
        lines.extend(param_str)

        lines.append(f"  function = transparent_{self.node_meta.node_type.name}(integration=\"{self.node_meta.integration_name}\", resource=\"{self.node_meta.resource_name}\", operation=\"{self.node_meta.operation_name}\")")
    
        if self.node_meta.node_type == NodeType.action:
            lines.append( "  output_data = function.run(input_data=input_data, params=params)")
        else:
            lines.append( "  output_data = function.run(input_data=None, params=params)")

        lines.append("  return output_data")

        return lines 
    
    def parse_parameters(self, param_json: dict) -> (n8nParamParseStatus, str):
        """对于一个输入的参数，检查是否符合params格式
        """
        new_params = deepcopy(self.params)
        for key in new_params:
            new_params[key].refresh()

        tool_call_result = []

        if not isinstance(param_json, dict):
            tool_status = n8nParamParseStatus.ParamTypeError
            return tool_status, json.dumps({"error": f"Parameter Type Error: The parameter is expected to be a json format string which can be parsed as dict type. However, you are giving string parsed as {type(param_json)}", "result": "Nothing happened.", "status": tool_status.name})

        for key in param_json.keys():
            if key not in new_params.keys():
                tool_status = n8nParamParseStatus.UndefinedParam
                return tool_status, json.dumps({"error": f"Undefined input parameter \"{key}\" for {self.get_name()}.Supported parameters: {list(new_params.keys())}", "result": "Nothing happened.", "status": tool_status.name})
            parse_status, parse_output = new_params[key].parse_value(param_json[key])
            if parse_status != n8nParamParseStatus.ParamParseSuccess:
                tool_status = parse_status
                return tool_status, json.dumps({"error": f"{parse_output}", "result": "Nothing Happened", "status": tool_status.name})
            tool_call_result.append(parse_output)

        #所有param都没问题，
        #TODO: 检查是否有required字段没给出

        self.params = new_params
        tool_status = n8nParamParseStatus.ParamParseSuccess

        self.update_implement_info()
        return tool_status, {"result": tool_call_result, "status": tool_status.name}

