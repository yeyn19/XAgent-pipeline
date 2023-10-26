"""在XAgent里给n8n做支持，和tool_call_handle对应
"""
import subprocess
import tempfile
import json
import traceback
from typing import Optional
import uuid

from XAgent.tools.n8n_tools.n8n_node import n8nPythonNode
from XAgent.tools.n8n_tools.n8n_credential_loader import n8n_credentials
from XAgent.logs import logger

success_prompt = """Execution was successful:
====================================
"""

error_prompt = """Error executing workflow. See log messages for details.

Execution error:
===================================="""


def _get_constant_workflow(input_data):
    # node trigger
    node_trigger_id = str(uuid.uuid4())
    node_trigger = {
        "id": node_trigger_id,
        "name": "Execute Workflow Trigger",
        "type": "n8n-nodes-base.executeWorkflowTrigger",
        "typeVersion": 1,
        "position": [0, 0],
        "parameters": {}
    }
    node_trigger_name = str(node_trigger["name"])
    # node code
    node_code_id = str(uuid.uuid4())
    node_code_jsCode = f"return {json.dumps(input_data)}"
    node_code = {
        "id": node_code_id,
        "name": "Code",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [180, 0],
        "parameters": {
            "jsCode": node_code_jsCode
        }
    }
    node_code_name = str(node_code["name"])

    #TODO: add type, type_versions, paramters, credentials
    node_var = {
        "id": str(uuid.uuid4()),
        "name": "node_var",
        "position": [360, 0],
    }

    workflow_connection = dict({
        node_trigger_name: {
            "main": [
                [
                    {
                        "node": node_code_name,
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        },
        node_code_name: {
            "main": [
                [
                {
                    "node": node_var["name"],
                    "type": "main",
                    "index": 0
                }
                ]
            ]
        }
    })
    
    workflow_nodes = [node_trigger,node_code, node_var]

    workflow_versionId = str(uuid.uuid4())
    workflow_name = "Simple Workflow"
    workflow = {
        # "id": workflow_id,
        "versionId": workflow_versionId,
        "name": workflow_name,
        "nodes": workflow_nodes,
        "connections": workflow_connection,
        "active": False,
        "settings": {
            "executionOrder": "v1"
        },
        "tags": []
    }

    return workflow

def run_node(node: n8nPythonNode, input_data: list[dict] = [{}]) -> tuple[str, str]:
    """Execute a specified node.

    Args:
        workflow_id (Optional[str], optional): ID of the workflow in which the node is located. The workflow ID must be in your n8n workflow database. You could create a workflow and pick that id. If not provided, the default workflow will be used. Defaults to None.
        node (Optional[dict], optional): n8n node json dictionary. If not provided, the default slack send message node will be used. Defaults to None.
        input_data (list[dict], optional): Input data for the node. Defaults to [{}].

    Returns:
        tuple[str, str]: A tuple containing two strings. The first string represents the status of the node execution (e.g., "success", "failure"), and the second string provides additional information or error messages related to the execution.
    """

    constant_workflow = _get_constant_workflow(input_data=input_data)

    constant_workflow["id"] = n8n_credentials.get_workflow_id()
    node_var = constant_workflow["nodes"][-1]
    node_var["type"] = "n8n-nodes-base." + node.node_meta.integration_name

    if n8n_credentials.query(node.node_meta.integration_name) != None:
        credential_item = n8n_credentials.query(node.node_meta.integration_name)
        node_var["credentials"] = {
            credential_item["type"]: {
                "id": credential_item["id"],
                "name": credential_item["name"],
            }
        }

    param_json = {}
    for key, value in node.params.items():
        param = value.to_json()
        if param != None:
            param_json[key] = param
    node_var["parameters"] = param_json


    node_var["parameters"]["operation"] = node.node_meta.operation_name
    node_var["parameters"]["resource"] = node.node_meta.resource_name

    if node.node_meta.integration_name == 'slack':
        node_var["parameters"]["authentication"] = "oAuth2"    
    if node.node_meta.integration_name == 'googleSheets':
        node_var["parameters"]["operation"] = node.node_meta.operation_name
        node_var["typeVersion"] = 4
        node_var["parameters"]["columns"] = {
                    "mappingMode": "autoMapInputData",
                    "value": {},
                    "matchingColumns": [
                      "id"
                    ]
                }


    # handle workflow

    if 'pseudoNode' in node.node_json.keys() and node.node_json['pseudoNode']:
        try:
            output = run_pseudo_workflow(input_data, constant_workflow)
            error= ""
        except BaseException as e:
            traceback.print_exc()
            print(e)
            raise e
    else:
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json")
        json.dump(constant_workflow, temp_file)
        # import pdb; pdb.set_trace()
        temp_file.close()
        temp_file_path = temp_file.name
        result = subprocess.run(["n8n", "execute", "--file", temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
        # Get the standard output
        output = result.stdout.decode('utf-8')
        error = result.stderr.decode('utf-8')

    logger.info("###OUTPUT###")
    print(output)

    logger.info("###ERROR###")
    print(error)

    output_data = ""
    error = ""

    # check input data
    if input_data == None or len(input_data) == 0:
        warning_prompt = "WARNING: There is nothing in input_data. This may cause the failure of current node execution.\n"
        print(colored(warning_prompt, color='yellow'))
        output_data += warning_prompt

    if success_prompt in output:
        output_data = output.split(success_prompt)[-1]
    else:
        assert error_prompt in output
        outputs = output.split(error_prompt)
        assert len(outputs) == 2
        output_data = outputs[0]
        error = outputs[1].strip()

    if output_data != "":

        output_data = json.loads(output_data)
        output_data = output_data["data"]["resultData"]["runData"]["node_var"][0]["data"]["main"][0]
    else:
        output_data = []

    # print(output_data)
    # print("===error===")
    # print(error)
    # exit()



    return output_data, error