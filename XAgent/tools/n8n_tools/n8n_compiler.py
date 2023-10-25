import json
from typing import List, Dict
from copy import deepcopy

from XAgent.logs import logger
from XAgent.tools.param_system import ParamSystem
from XAgent.tools.n8n_tools.n8n_utils import NodeType, n8nNodeMeta
from XAgent.tools.n8n_tools.n8n_node import n8nPythonNode
from XAgent.tools.n8n_tools.n8n_param_parser import parse_properties


class n8nCompiler():
    """和nodes.json交互，同时存储目前所有的数据结构
    """


    def __init__(self):
        self.resolve()



    def resolve_integration(self, integration_json):
        
        integration_name = integration_json["name"].split(".")[-1]
        integration_data = {}
        no_resource = True
        no_operation = True
        for property in integration_json["properties"]:
            if property["name"] == "resource":
                for resource in property["options"]:
                    integration_data[resource["value"]] = {}
                no_resource = False
                break

        # 有些简单integration没有resource，我们认为resource=default
        if no_resource:
            integration_data["default"] = {}
        

        for property in integration_json["properties"]:
            if property["name"] == "operation":
                target_resource_name = "default"
                if "displayOptions" in property.keys():
                    assert "show" in property["displayOptions"].keys() and "resource" in property["displayOptions"]["show"].keys()
                    assert len(property["displayOptions"]["show"]["resource"]) == 1
                    target_resource_name = property["displayOptions"]["show"]["resource"][0]
                    # print()
                    assert target_resource_name in integration_data.keys(), f"{target_resource_name} in {integration_data.keys()}"

                target_resource = integration_data[target_resource_name]
                for operation in property["options"]:
                    operation_name = operation["value"]
                    operation_description = ""
                    if "description" in operation.keys():
                        operation_description = operation["description"]
                    node_type = NodeType.trigger if "trigger" in integration_name.lower() or "webhook" in integration_name.lower() else NodeType.action
                    target_resource[operation_name] = n8nNodeMeta(
                                                                node_type=node_type,
                                                                integration_name=integration_name,
                                                                resource_name=target_resource_name,
                                                                operation_name=operation_name,
                                                                operation_description=operation_description
                                                            )
                    no_operation = False
        # 有些简单integration没有operation，我们认为action=default
        if no_operation:
            assert no_resource
            node_type = NodeType.trigger if "trigger" in integration_name.lower() or "webhook" in integration_name.lower() else NodeType.action
            integration_data["default"]["default"] = n8nNodeMeta(
                                                                node_type=node_type,
                                                                integration_name=integration_name,
                                                                resource_name="default",
                                                                operation_name="default",
                                                                operation_description=""
                                                            )

        return integration_data

    def print_flatten_tools(self):
        output_description_list = []
        for k1, integration_name in enumerate(list(self.flattened_tools.keys())):
            operation_counter = 1
            data = self.flattened_tools[integration_name]["data"]
            des = self.flattened_tools[integration_name]["meta"]["description"]
            # if integration_name in CONFIG.default_knowledge.keys():
            #     print(colored(f"{integration_name} knowledge is found!", color='light_yellow'))
            #     des += CONFIG.default_knowledge[integration_name]

            output_description_list.append(f"{k1+1}.integration={integration_name}: {des}")
            for k2,resource in enumerate(list( data.keys())):
                for k3, operation in enumerate(list(data[resource].keys())):
                    new_line = f"  {k1+1}.{operation_counter}: " + data[resource][operation].to_action_string()
                    operation_counter += 1
                    output_description_list.append(new_line)
        
        return "\n".join(output_description_list)



    def resolve(self):
        # print(self.cfg.parser.nodes_whtie_list)
        self.json_data = []
        self.flattened_tools = {}
        white_list = [
            "slack.message.post",
            "googleSheets.sheet.read",
            "gmail.message.send",
        ]
        nodes_json_path = "XAgent/tools/n8n_tools/n8n_nodes.json"

        available_integrations = [item.split(".")[0] for item in white_list]
        with open(nodes_json_path, "r", encoding="utf-8") as reader:
            integrations = json.load(reader)
            for integration_json in integrations:
                name = integration_json["name"].split(".")[-1]
                if name not in available_integrations:
                    continue
                self.json_data.append(integration_json)
                integration_data = self.resolve_integration(integration_json=integration_json)
                index = available_integrations.index(name)
                full_tool = white_list[index]
                splits = full_tool.split(".")
                if len(splits) > 1: #指定了resource，别的不行
                    for key in list(integration_data.keys()):
                        if key != splits[1]:
                            integration_data.pop(key)
                    if len(splits) == 3:
                        for action in list(integration_data[splits[1]].keys()):
                            if action != splits[2]:
                                integration_data[splits[1]].pop(action)

                integration_description = integration_json["description"] if "description" in integration_json.keys() else ""
                self.flattened_tools[name] = {
                    "data": integration_data,
                    "meta": {
                        "description": integration_description,
                        "node_json": integration_json,
                    },
                    "pseudoNode": integration_json['pseudoNode'] if "pseudoNode" in integration_json.keys() else False
                }
                if self.flattened_tools[name]['pseudoNode']:
                    print(colored(f"load pseudoNode {name}", color='cyan'))
        out = self.print_flatten_tools()
        print(out)

    def get_n8n_node(self, integration_name, resource_name, operation_name):
        node_type = self.flattened_tools[integration_name]["data"][resource_name][operation_name].node_type

        new_node = n8nPythonNode(
                        node_meta=deepcopy(self.flattened_tools[integration_name]["data"][resource_name][operation_name]),
                        node_json=self.flattened_tools[integration_name]["meta"]["node_json"],
                    )
        new_node.params = parse_properties(new_node)
        new_node.update_implement_info()
        return new_node

n8n_compiler = n8nCompiler() 