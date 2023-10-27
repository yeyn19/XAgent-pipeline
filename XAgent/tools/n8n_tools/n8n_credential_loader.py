import os
import json
from typing import Dict, Any

class n8nCredentials():
    def __init__(self, base_file_path= "./XAgent/tools/n8n_tools/n8n_credentials"):
        with open(os.path.join(base_file_path,"c.json"),"r") as reader:
            credential_data = json.load(reader)
            self.credential_data: Dict[str,Any] = {}
            for item in credential_data:
                item_info = {
                    "name": item["name"],
                    "id": item["id"],
                    "type": item["type"],
                }
                for node_type in item["nodesAccess"]:
                    node_type_name = node_type["nodeType"].split(".")[-1]
                    if self.credential_data.get(node_type_name,-1) == -1:
                        self.credential_data[node_type_name] = []
                    self.credential_data[node_type_name].append(item_info)
        with open(os.path.join(base_file_path,"w.json"),"r") as reader:
            workflow_data = json.load(reader)
            self.workflow_id = workflow_data[0]["id"]
                
    def get_workflow_id(self) -> str:
        """根据本机操作系统，选择不同
        """
        return self.workflow_id

    def query(self, node_type):
        if self.credential_data.get(node_type,-1) == -1:
            return None
        return self.credential_data[node_type][-1]
 
n8n_credentials = n8nCredentials()