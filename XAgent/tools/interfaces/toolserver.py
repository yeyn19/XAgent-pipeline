import os
import json
import requests
from typing import Tuple
from colorama import Fore
from concurrent.futures import ThreadPoolExecutor

from XAgent.logs import logger
from XAgent.ai_functions import function_manager
from XAgent.enums import ToolCallStatusCode
from .base import BaseToolInterface
from .utils import unwrap_tool_response


class ToolServerInterface(BaseToolInterface):
    def lazy_init(self, config):
        self.config = config
        if config.selfhost_toolserver_url is not None:
            self.url = config.selfhost_toolserver_url
        else:
            raise NotImplementedError('Please use selfhost toolserver')
        logger.typewriter_log("ToolServer connected in", Fore.GREEN, self.url)
        response = requests.post(f'{self.url}/get_cookie',)
        self.cookies = response.cookies

    
        return self

    def close(self):
        self.download_all_files()
        requests.post(f'{self.url}/close_session', cookies=self.cookies)

    def upload_file(self, file_path) -> str:
        url = f"{self.url}/upload_file"
        response = requests.post(url,
                                 timeout=10,
                                 cookies=self.cookies,
                                 files={'file': open(file_path, 'rb'), 'filename': os.path.basename(file_path)})
        response.raise_for_status()
        response = response.json()
        return response

    def download_file(self, file_path) -> str:
        url = f"{self.url}/download_file"
        payload = {
            'file_path': file_path
        }
        response = requests.post(
            url, json=payload, timeout=10, cookies=self.cookies,)
        response.raise_for_status()

        save_path = os.path.join(self.config.record_dir, file_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path

    def get_workspace_structure(self) -> dict:
        url = f"{self.url}/get_workspace_structure"
        response = requests.post(url, timeout=10, cookies=self.cookies,)
        response.raise_for_status()
        response = response.json()
        return response

    def download_all_files(self):
        url = f"{self.url}/download_workspace"
        response = requests.post(url, cookies=self.cookies,)
        response.raise_for_status()

        save_path = os.path.join(self.config.record_dir, 'workspace.zip')
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path

    def get_available_tools(self,reload=False)->Tuple[list[str],dict]:
        if hasattr(self, 'available_tools') and not reload:
            return self.tools['available_tools'],self.tools['tools_json']

        url = f"{self.url}/get_available_tools"
        payload = {}
        response = requests.post(
            url, json=payload, timeout=10, cookies=self.cookies)
        response.raise_for_status()
        response = response.json()
        if not isinstance(response, dict):
            response = json.loads(response)
            
        for tool in response['tools_json']:
            function_manager.register_function(tool)
        
        match self.config.default_request_type:
            case 'openai':
                subtask_handle = function_manager.get_function_schema('subtask_handle')
                subtask_handle['parameters']['properties']['tool_call']['properties']['tool_name']['enum']=response['available_tools']

            case 'xagent':
                pass
            case _:
                raise NotImplementedError(f'Request type {self.config.default_request_type} not implemented')
        response['available_tools'] = list(filter(lambda x: x not in self.config.tool_blacklist, response['available_tools']))
        response['tools_json'] = list(filter(lambda x: x['name'] not in self.config.tool_blacklist, response['tools_json']))
        self.tools = response
        return self.tools['available_tools'],self.tools['tools_json']
    
    def get_schema_for_tools(self, tool_names: list[str], schema_type: str = "json"):
        url = f"{self.url}/get_{schema_type}_schema_for_tools"
        payload = {"tool_names": tool_names}

        response = requests.post(
            url, json=payload, timeout=10, cookies=self.cookies)
        response.raise_for_status()
        response = response.json()
        if not isinstance(response, dict) and isinstance(response, str):
            response = json.loads(response)

        function_manager.register_function(response)
        return response

    def summary_webpage(self, result, args: dict):
        if isinstance(result, list):
            with ThreadPoolExecutor(max_workers=len(result)) as pool:
                f = []
                for ret in result:
                    f.append(pool.submit(function_manager, 'parse_web_text',
                             webpage=ret['page'][:8096], prompt=args['goals_to_browse']))
                for ret, thd in zip(result, f):
                    ret['page'] = thd.result()
                    ret['page']['useful_hyperlinks'] = ret['page']['useful_hyperlinks'][:3]
        else:
            if not isinstance(result, str):
                result = str(result)
            result = function_manager(
                'parse_web_text', webpage=result[:8096], prompt=args['goals_to_browse'])
            result['useful_hyperlinks'] = result['useful_hyperlinks'][:3]
        return result

    def execute(self, tool_name: str, **kwargs):
        url = f"{self.url}/execute_tool"
        if isinstance(kwargs, str):
            try:
                kwargs = json.loads(kwargs)
            except:
                pass
        payload = {
            "tool_name": tool_name,
            "arguments": kwargs,
        }

        response = requests.post(url, json=payload, cookies=self.cookies)

        if response.status_code == 200 or response.status_code == 450:
            output = response.json()
            output = unwrap_tool_response(output)
        else:
            output = response.text

        match response.status_code:
            case 200:
                status_code = ToolCallStatusCode.TOOL_CALL_SUCCESS
            case 404:
                status_code = ToolCallStatusCode.HALLUCINATE_NAME
            case 422:
                status_code = ToolCallStatusCode.FORMAT_ERROR
            case 450:
                status_code = ToolCallStatusCode.TIMEOUT_ERROR
            case 500:
                status_code = ToolCallStatusCode.TOOL_CALL_FAILED
            case 503:
                raise Exception("Server Error: "+output)
            case _:
                status_code = ToolCallStatusCode.OTHER_ERROR

        if 'WebEnv' in tool_name:
            output = self.summary_webpage(output, kwargs)
        return status_code,output
