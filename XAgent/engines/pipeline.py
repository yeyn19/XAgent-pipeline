from typing import Any,Tuple
import os
import json
from colorama import Fore, Style

from XAgent.config import CONFIG
from XAgent.tools import ToolServerInterface, BuiltInInterface, n8nToolInterface, CustomizedToolInterface
from XAgent.agent import RouteAgent
from XAgent.agent.summarize import summarize_action,summarize_plan,clip_text
from XAgent.logs import logger
from XAgent.utils import has_user_provide_route_function
from XAgent.models import ExecutionNode,ExecutionGraph, ToolCall, PipelineTaskNode, Plan, ReActExecutionGraph
from XAgent.enums import ToolType, RequiredAbilities
from XAgent.global_vars import INTERRUPT,agent_dispatcher
from .base import BaseEngine

from XAgent.models.pipeline_automat import *

    



def default_route_node(now_node: PipelineAutoMatNode, pipeline: PipelineAutoMat, runtime_stack: PipelineRuntimeStackUserInterface) -> PipelineRouteResult:
    """再该执行完以后，决定下一个node是什么，做route等事情
    """
    all_next_edges = pipeline.get_adjacent_node(now_node)
    all_next_edges = [pipeline[now_node.node_id,gid] for gid in all_next_edges]
    for out_edge in all_next_edges:

        if has_user_provide_route_function(out_edge):
            route_result: PipelineRouteResult = out_edge.route(pipeline, runtime_stack)
            # import pdb; pdb.set_trace()
            if route_result.select_this_edge:
                return route_result
    return PipelineRouteResult(
        select_this_edge=False
    )



class PipelineEngine(BaseEngine):
    """Execute a pipeline as a automat."""
    def __init__(self, config=CONFIG):
        super().__init__(config)

        self.toolserverif = ToolServerInterface()
        self.n8nif = n8nToolInterface()
        self.customif = CustomizedToolInterface()
        self.toolifs = [self.toolserverif, self.n8nif, self.customif]

        self.route_agent = agent_dispatcher.dispatch(RequiredAbilities.route_pipeline,None)
    

    async def step(self,
                   node: PipelineAutoMatNode,
                   route_result: PipelineRouteResult,
                   force_stop:bool=False,
                   interrupt:bool=False,
                   *args,**kwargs)->ExecutionNode:
        match node.node_type:

            case ExecutionNodeTypeForPipelineUserInterface.ToolServer | ExecutionNodeTypeForPipelineUserInterface.N8N | ExecutionNodeTypeForPipelineUserInterface.Custom:
                prior_tool_node = ToolCall()
                prior_tool_node.set_tool(
                    tool_name=node.tool_name,
                    tool_args=route_result.provide_params,
                )
                status_code, output_data = await self.execute(prior_tool_node)
                return status_code, output_data, prior_tool_node
            case ExecutionNodeTypeForPipelineUserInterface.ReACTChain:
                from .react import ReActEngine
                temp_react_engine = ReActEngine(CONFIG)
                execute_graph: ReActExecutionGraph = await temp_react_engine.run(
                    task= TaskNode(
                        plan = Plan.get_single_subtask_plan_from_task(query=route_result.provide_params["query"])
                    )
                )


            case _:
                logger.typewriter_log("Not implemented", Fore.RED, node.node_type.name)
                raise NotImplementedError
    
    def ai_route_function(self, task_node: PipelineTaskNode, now_node: PipelineAutoMatNode, pipeline: PipelineAutoMat, runtime_stack: PipelineRuntimeStackUserInterface, target_node: PipelineAutoMatNode = None):
        _,file_archi = self.toolserverif.execute("FileSystemEnv_print_filesys_struture",return_root=True)
        file_archi,_ = clip_text(file_archi,1000,clip_end=True)
        node_info = now_node.to_json()
        edge_info = pipeline.describe_outedge_json(now_node=now_node)
        # import pdb; pdb.set_trace()
        message,_ = self.route_agent.parse(
            placeholders={
                "system": {
                    "query_overview": task_node.overall_task_description,
                    "pipeline_overview": pipeline,

                },
                "user": {
                    "workspace_files":file_archi,
                    "node_info": json.dumps(node_info, indent=2, ensure_ascii=False),
                    "edge_info": json.dumps(edge_info, indent=2, ensure_ascii=False),
                }
            },
            arguments=function_manager.get_function_schema('action_reasoning')['parameters'],
            functions=self.tools_schema+functions,
            function_call={'name':finish_tool_call} if force_stop else None,
            additional_messages=messages,
            additional_insert_index=-1
        )


    async def run(self,task: PipelineTaskNode,

                  **kwargs)->ExecutionGraph:
        out_names, out_json = await self.get_available_tools()
        # print(json.dumps(out_json,indent=2))
        """传入pipeline文件，执行pipeline"""
        pipeline_dir = task.pipeline_dir
        file = pipeline_dir.replace("/",".") + ".rule"
        with open(os.path.join(pipeline_dir,"automat.json")) as reader:
            pipeline_json_data = json.load(reader)
        pipeline = PipelineAutoMat.from_json(
            json_data=pipeline_json_data,
            rule_file_name=file,
        )

        query = task.overall_task_description

        visit_count = 0
        now_node = pipeline.get_begin_node() #start_node不需要执行，直接route
        while True:
            all_next_nodes = pipeline.get_adjacent_node(now_node)
            all_next_nodes = [pipeline[gid] for gid in all_next_nodes]

            if len(all_next_nodes) == 1: 
                logger.typewriter_log(
                    "pipeline running to the end",
                    Fore.YELLOW
                )
                break
            route_result: PipelineRouteResult = None
            route_type: PipelineRouteType = PipelineRouteType.RuleBasedSelectAndParam
            if has_user_provide_route_function(now_node): 
                logger.typewriter_log(
                    f"use User-provided route function for node \"{now_node.node_name}\"",
                    Fore.YELLOW,
                )
                user_route_result: PipelineRouteResult = now_node.route(pipeline, pipeline.runtime_info)
                if user_route_result.select_node != None:
                    route_result = user_route_result
            else:
                logger.typewriter_log(
                    f"use default route function for node \"{now_node.node_name}\"",
                    Fore.YELLOW,
                )
                default_route_result = default_route_node(now_node, pipeline, pipeline.runtime_info)
                if default_route_result.select_this_edge:
                    route_result = default_route_result
            
            if not route_result:
                logger.typewriter_log(
                    f"use AI-route-function for node \"{now_node.node_name}\" to provide both selection and params",
                    Fore.YELLOW,
                )
                route_result = self.ai_route_function(task, now_node, pipeline, pipeline.runtime_info)
                route_type = PipelineRouteType.AISelectAndGiveParam
            assert route_result != None

            next_node = route_result.to_node
            logger.typewriter_log(
                f"pipeline newly select node \"{next_node.node_name}\":",
                Fore.YELLOW,
                f"{next_node.node_type.value}.{next_node.tool_name}"
            )

            if not route_result.param_sufficient:
                logger.typewriter_log(
                    f"use AI-route-function for node \"{now_node.node_name}\" to provide tool params",
                    Fore.YELLOW,
                )
                route_result = self.ai_route_function(task, now_node, pipeline, pipeline.runtime_info, target_node=next_node)
                route_type = PipelineRouteType.AIGiveParam
            assert route_result.param_sufficient

            #执行工具调用
            status_code, output_data, prior_tool_node = await self.step(next_node, route_result)
            
            runtime_node = PipelineRuntimeNode(
                                route_result=route_result,
                                route_type=route_type,
                                tool_node=prior_tool_node,
                                )
            pipeline.runtime_info.runtime_stack.append(runtime_node)
            next_node.runtime_stack.append(runtime_node)

            now_node = next_node
            visit_count += 1
        
        
        
        
        