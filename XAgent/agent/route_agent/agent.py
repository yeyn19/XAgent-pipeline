import json
import json5
import jsonschema
from typing import List
from colorama import Fore
from tenacity import retry, stop_after_attempt

from XAgent.agent.base_agent import BaseAgent
from XAgent.enums import RequiredAbilities
from XAgent.message_history import Message
from XAgent.logs import logger
from XAgent.models import ToolCall
from XAgent.ai_functions import function_manager,objgenerator
from XAgent.config import CONFIG

class RouteAgent(BaseAgent):
    abilities = set([RequiredAbilities.route_pipeline])
    
    
    @retry(stop=stop_after_attempt(CONFIG.max_retry_times),reraise=True)
    def parse(
        self,
        placeholders: dict = {},
        arguments:dict=None,
        functions=None,
        function_call=None,
        stop=None,
        additional_messages: List[Message] = [],
        additional_insert_index: int = -1,
        *args,
        **kwargs
    ):
        prompt_messages = self.fill_in_placeholders(placeholders)
        messages = prompt_messages[:additional_insert_index] + additional_messages + prompt_messages[additional_insert_index:]
        messages = [message.raw() for message in messages]
        import pdb; pdb.set_trace()
        # Temporarily disable the arguments for openai
        if self.config.default_request_type == 'openai':
            arguments = None
            functions = list(filter(lambda x: x['name'] not in ['subtask_submit','subtask_handle'],functions))
            if CONFIG.enable_ask_human_for_help:
                functions += [function_manager.get_function_schema('ask_human_for_help')]
            messages[0]['content'] += '\n--- Avaliable Tools ---\nYou are allowed to use tools in the "subtask_handle.tool_call" function field.\nRemember the "subtask_handle.tool_call.tool_input" field should always in JSON, as following described:\n{}'.format(json.dumps(functions,indent=2))
            
            functions = [function_manager.get_function_schema('subtask_submit'),
                         function_manager.get_function_schema('subtask_handle')]

        message,tokens = self.generate(
            messages=messages,
            arguments=arguments,
            functions=functions,
            function_call=function_call,
            stop=stop,
            *args,**kwargs
        )

        function_call_args:dict = message['function_call']['arguments']

        # for tool_call, we need to validate the tool_call arguments if exising
        if self.config.default_request_type == 'openai' and 'tool_call' in function_call_args:
            tool_schema = function_manager.get_function_schema(function_call_args['tool_call']["tool_name"])
            assert tool_schema is not None, f"Function {function_call_args['tool_call']['tool_name']} not found! Poential Schema Validation Error!"
            
            tool_call_args = function_call_args['tool_call']['tool_input'] if 'tool_input' in function_call_args['tool_call'] else ''
            
            def validate():
                nonlocal tool_schema,tool_call_args
                if isinstance(tool_call_args,str):
                    tool_call_args = {} if tool_call_args == '' else json5.loads(tool_call_args)
                jsonschema.validate(instance=tool_call_args, schema=tool_schema['parameters'])
            
            try:
                validate()
            except Exception as e:  
                messages[0] = change_tool_call_description(messages[0],reverse=True)
                tool_call_args = objgenerator.dynamic_json_fixs(
                    broken_json=tool_call_args,
                    function_schema=tool_schema,
                    messages=messages,
                    error_message=str(e))["choices"][0]["message"]["function_call"]["arguments"]
                validate()
            
            function_call_args['tool_call']['tool_input'] = tool_call_args
            
            message['function_call'] = function_call_args.pop('tool_call')
            message['function_call']['name'] = message['function_call'].pop('tool_name')
            message['function_call']['arguments'] = message['function_call'].pop('tool_input')
            message['arguments'] = function_call_args
                
        return message,tokens
    
    def message_to_toolcall(self,message) -> ToolCall:
        # assume message format
        # {
        #   "content": "The content is useless",
        #   "function_call": {
        #       "name": "xxx",
        #       "arguments": "xxx"
        #  },
        #  "arguments": {
        #      "xxx": "xxx",
        #      "xxx": "xxx"   
        #  },
        # }
        
        toolcall = ToolCall()
        if "content" in message.keys():
            print(message["content"])
            toolcall.data["content"] = message["content"]
        if 'arguments' in message.keys():
            toolcall.data['thoughts']['properties'] = message["arguments"]
        if "function_call" in message.keys():
            toolcall.data["command"]["properties"]["name"] = message["function_call"]["name"]
            toolcall.data["command"]["properties"]["args"] = message["function_call"]["arguments"]
        else:
            logger.typewriter_log("message_to_toolcall warning: no function_call in message",Fore.RED)

        return toolcall