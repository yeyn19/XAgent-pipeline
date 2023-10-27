from typing import Any, Tuple
import orjson
import json5
import traceback

from colorama import Fore,Style
from XAgent.config import CONFIG

from XAgent.logs import logger,print_task_save_items
from XAgent.agent.summarize import summarize_action,summarize_plan,clip_text
from XAgent.global_vars import INTERRUPT,agent_dispatcher
from XAgent.ai_functions import function_manager
from XAgent.utils import TaskSaveItem
from XAgent.running_recorder import recorder
from XAgent.tools import ToolServerInterface

from XAgent.models import Plan,PlanExecutionNode,PlanExecutionGraph,TaskNode, ToolCall
from XAgent.enums import RequiredAbilities,EngineExecutionStatusCode,TaskStatusCode,PlanOperationStatusCode
from XAgent.message_history import Message


from .base import BaseEngine,ExecutionGraph,ExecutionNode

class PlanEngine(BaseEngine):
    def __init__(self, config=CONFIG):
        super().__init__(config)
        self.plan_inital_agent = agent_dispatcher.dispatch(RequiredAbilities.plan_generation,None)
        self.plan_rectify_agent = agent_dispatcher.dispatch(RequiredAbilities.plan_refinement,None)
        self.reflection_agent = agent_dispatcher.dispatch(
            RequiredAbilities.reflection,
            "Reflect on the previous actions and give the posterior knowledge"
        )
                
        self.thought_arguments = function_manager.get_function_schema('simple_thought')['parameters']
        self.generate_inital_plan_function = function_manager.get_function_schema('subtask_split_operation')
        self.plan_rectify_function = function_manager.get_function_schema('subtask_operations')
        self.reflection_arguments = function_manager.get_function_schema('generate_posterior_knowledge')['parameters']
    
    async def step(self,
                   task:PlanExecutionNode,
                   plan:Plan,
                   execution_engine:BaseEngine,
                   *,
                   force_stop:bool=False,
                   interrupt:bool=False,
                   **kwargs)->PlanExecutionNode:
        """Step and return execution result."""
        
        task_id = plan.get_subtask_id(to_str=True)
        recorder.change_now_task(task_id)
        plan.data.status = TaskStatusCode.DOING
        
        logger.typewriter_log(
            f"-=-=-=-=-=-=-= Performing Task {task_id} ({plan.data.name}): Begin -=-=-=-=-=-=-=",
            Fore.GREEN,
            "",
        )
        print_task_save_items(plan.data)
        
        if interrupt:
            logger.typewriter_log("-=-=-=-=-=-=-= INTERRUPTED -=-=-=-=-=-=-=",Fore.RED,)
            from XAgent.global_vars import INTERRUPT_MESSAGE
            # TODO: add interrupt message
            # message:str = await INTERRUPT_MESSAGE.get()



        exec_result = await execution_engine.run(
            task=TaskNode(plan=plan),
            plans=task.plan.to_json(),
            **kwargs)
        
        actions = list(map(lambda x:getattr(x,'tool_call').to_json(),exec_result.get_execution_track()))
        exec_node = PlanExecutionNode(
            role=task.role,
            task=plan.data.name,
            plan=plan,
            actions=actions,
        )

        plan.data.status = TaskStatusCode.SUCCESS if exec_result.status == EngineExecutionStatusCode.SUCCESS else TaskStatusCode.FAIL
        exec_node.status_code = plan.data.status
        
        logger.typewriter_log(
            f"-=-=-=-=-=-=-= Task {task_id} ({plan.data.name}): {plan.data.status.value} -=-=-=-=-=-=-=",
            plan.data.status.color(),
        )

        plan = await self.posterior_process(task=exec_node,
                                last_plan=plan,
                                tools_schema=execution_engine.available_tools)
        
        if getattr(exec_result,'need_for_plan_refine',False):
            task = await self.plan_rectify(
                task,
                plan,
                exec_result,
                execution_engine)
        
        exec_node.end_node = plan.pop_next_subtask(plan) is None
            
        # TODO: This part should be improved to reduce the interaction with other packages
        try:
            import uuid
            from XAgentServer.interaction import XAgentInteraction
            server_interaction:XAgentInteraction = kwargs['interaction']
            update_data = plan.data.to_json(posterior=True)
            task_id = plan.get_subtask_id(to_str=True)
            update_data['task_id'] = task_id
            await server_interaction.update_cache(
                update_data=update_data, 
                status="refinement", 
                current=task_id)
            
            # update remaining task
            if exec_node.end_node:
                await kwargs['interaction'].update_cache(update_data=[], status="finished")
            else:
                subtask_list = []
                remaining_subtask:list[Plan] = plan.get_remaining_subtask(plan)
                for todo_plan in remaining_subtask:
                    raw_data = todo_plan.data.to_json(posterior=True)
                    raw_data.pop('action_list_summary',None)
                    raw_data.pop('posterior_plan_reflection',None)
                    raw_data.pop('tool_reflection',None)
                    raw_data["task_id"] = todo_plan.get_subtask_id(to_str=True)
                    raw_data["inner"] = []
                    raw_data["node_id"] = uuid.uuid4().hex
                    subtask_list.append(raw_data)
                await server_interaction.update_cache(update_data=subtask_list, status="subtask", current=task_id)
        except:
            traceback.print_exc()

        
        return exec_node
    
    async def run(self,task:PlanExecutionNode,execution_engine:BaseEngine,**kwargs)->PlanExecutionGraph:
        """Execute the engine and return the result node."""
        await self.lazy_init(self.config)
        task = await self.generate_inital_plan(task,execution_engine.available_tools)
        
        inital_plan = task.plan.to_json()
        logger.typewriter_log("INITIAL PLAN: ",Fore.BLUE)
        print(summarize_plan(inital_plan))
        
        # TODO: This part should be improved to reduce the interaction with other packages
        try:
            import uuid
            from XAgentServer.models.ws import XAgentOutputData
            from XAgentServer.interaction import XAgentInteraction
            server_interaction:XAgentInteraction = kwargs['interaction']
            server_interaction.init_cache(data=XAgentOutputData())
            await server_interaction.update_cache(update_data={
                "node_id": uuid.uuid4().hex,
                "task_id": inital_plan.get("task_id", ""),
                "name": inital_plan.get("name", ""),
                "goal": inital_plan.get("goal", ""),
                "handler": inital_plan.get("handler", ""),
                "tool_budget": inital_plan.get("tool_budget", ""),
                "subtasks": inital_plan.get("subtask", [])
            }, status="start", current=inital_plan.get("task_id", ""))
        except:
            traceback.print_exc()
            
        execution_track = PlanExecutionGraph()
        execution_track.set_begin_node(task)
        
        node = task
        while not node.end_node:
            nnode = await self.step(
                task=task,
                plan=task.plan.pop_next_subtask(node.plan),
                execution_engine=execution_engine,
                interrupt = INTERRUPT,
                **kwargs)
            
            execution_track.add_node(nnode)
            execution_track.add_edge(node,nnode)
            node = nnode
        
        execution_track.set_end_node(node)
        execution_track.status = EngineExecutionStatusCode.SUCCESS if node.status_code == TaskStatusCode.SUCCESS else EngineExecutionStatusCode.FAIL
    
        logger.typewriter_log("ALL Tasks Done", Fore.GREEN)
        return execution_track

    async def generate_inital_plan(self,task:PlanExecutionNode,available_tools:list[str]=[])->PlanExecutionNode:
        """Generate a plan."""
        logger.typewriter_log(
            "-=-=-=-=-=-=-= BEGIN PLAN GENERATION -=-=-=-=-=-=-=",
            Fore.GREEN,
            "",
        )
        logger.typewriter_log("Role",Fore.CYAN,task.role)
        logger.typewriter_log("Task",Fore.CYAN,task.task)
        
        if task.plan is None:
            task.plan = Plan(
                data = TaskSaveItem(
                    name=f"act as {task.role}",
                    goal=task.task,
                    milestones=[],
                )
            )
        
        message,_ = self.plan_inital_agent.parse(
            placeholders={
                "system": {
                    "avaliable_tool_names": available_tools,
                },
                "user": {
                    "query": orjson.dumps(task.plan.data.to_json()).decode(),
                }
            },
            arguments=self.thought_arguments,
            functions=[self.generate_inital_plan_function], 
            function_call={'name':self.generate_inital_plan_function['name']}
        )
        for subtask in json5.loads(message['function_call']['arguments'])['subtasks']:
            subtask = TaskSaveItem().load_from_json(function_output_item=subtask)
            task.plan.make_relation(task.plan,Plan(data=subtask))

        return task
    
    async def execute(self, tool_call: ToolCall,plans:Plan,current_task:Plan) -> Tuple[PlanOperationStatusCode, str]:
        
        print(tool_call.tool_args)
        tasks_inorder:list[Plan] = plans.get_inorder_travel(plans)
        tasks_ids = [task.get_subtask_id(to_str=True) for task in tasks_inorder]
        target_task_id = str(tool_call.tool_args['target_subtask_id']).strip()
        current_task_id = current_task.get_subtask_id(to_str=True)
        
        if target_task_id < current_task_id:
            return PlanOperationStatusCode.MODIFY_FORMER_PLAN,f"Cannot modify the task {target_task_id} which is before the current task {current_task_id}. Nothing happens."
        
        try:
            target_task = tasks_inorder[tasks_ids.index(target_task_id)]
        except ValueError:
            return PlanOperationStatusCode.TARGET_SUBTASK_NOT_FOUND,f"Cannot find the task {target_task_id}. Nothing happens."
         
        match tool_call.tool_args['operation']:
            case 'split':
                if target_task.get_depth() >= self.config.max_plan_tree_depth:
                    return PlanOperationStatusCode.OTHER_ERROR, f"Cannot split the task {target_task_id} which is too deep. Nothing happens."
                target_task.children = [Plan(father=target_task,data=TaskSaveItem().load_from_json(newtask)) for newtask in tool_call.tool_args['subtasks']]

                target_task.data.status = TaskStatusCode.SPLIT
                return PlanOperationStatusCode.MODIFY_SUCCESS,f"Split the task {target_task_id} successfully."

            case 'add':
                if target_task.get_depth() <= 1:
                    return PlanOperationStatusCode.OTHER_ERROR, f"Cannot add a task to the task {target_task_id} which is too shallow. Nothing happens."
                if len(target_task.father.children) + len(tool_call.tool_args['subtasks']) > self.config.max_plan_tree_width:
                    return PlanOperationStatusCode.OTHER_ERROR, f"Cannot add a task to the task {target_task_id} which is too wide. Nothing happens."
                newtasks = [Plan(father=target_task.father,data=TaskSaveItem().load_from_json(newtask)) for newtask in tool_call.tool_args['subtasks']]
                index_of_target_task = target_task.father.children.index(target_task)
                target_task.father.children = target_task.father.children[:index_of_target_task+1] + newtasks + target_task.father.children[index_of_target_task+1:]
                return PlanOperationStatusCode.MODIFY_SUCCESS,f"New tasks has been added after task {target_task_id} successfully."
            case 'delete':
                if target_task.data.status != TaskStatusCode.TODO :
                    return PlanOperationStatusCode.OTHER_ERROR, f"Cannot delete the task {target_task_id} which is not a TODO task. Nothing happens."
                target_task.father.children.remove(target_task)
                target_task.father = None
                return PlanOperationStatusCode.MODIFY_SUCCESS,f"Delete the task {target_task_id} successfully."
                
            case 'exit':
                return PlanOperationStatusCode.PLAN_REFINE_EXIT,'Exit the plan rectify process successfully.'
            case _:
                message = f"Operation {tool_call.tool_args['operation']} not found. Nothing happens."
                logger.typewriter_log("Error: ", Fore.RED, message)
                return PlanOperationStatusCode.PLAN_OPERATION_NOT_FOUND,message

        
        return PlanOperationStatusCode.OTHER_ERROR,'Unknown error'
    
    
    async def plan_rectify(self,task:PlanExecutionNode,plan:Plan,exec_result:ExecutionGraph,execution_engine:BaseEngine)->PlanExecutionNode:
        logger.typewriter_log(
            f"-=-=-=-=-=-=-= ITERATIVELY REFINE PLAN BASED ON TASK AGENT SUGGESTIONS -=-=-=-=-=-=-=",
            Fore.GREEN,
        )
        
        is_modified = False
        modify_steps = 0
        max_step = self.config.max_plan_refine_chain_length
        operations:list[ToolCall] = []
        
        try:
            refine_node_message = exec_result.get_end_node().tool_call.tool_args["suggestions_for_latter_subtasks_plan"]["reason"]
        except:
            traceback.print_exc()
            refine_node_message = ""
        try:
            _,file_archi = ToolServerInterface().execute("FileSystemEnv_print_filesys_struture",return_root=True)
            file_archi,_ = clip_text(str(file_archi),1000,clip_end=True)
        except:
            traceback.print_exc()
            file_archi = ""
            
        while modify_steps < max_step:
            modify_steps += 1
            logger.typewriter_log(
                f"-=-=-=-=-=-=-= Continually refining planning (still in the loop) -=-=-=-=-=-=-=",
                Fore.BLUE,
            )
            
            additional_messages = []
            if self.config.enable_summary: 
                init_message = summarize_plan(plan.to_json())
            else:
                init_message = orjson.dumps(plan.to_json()).decode()
            init_message =  Message("user", f"""The initial plan and the execution status is:\n{init_message}\n""")
            additional_messages.append(init_message)
            
            for k, operation in enumerate(operations):
                operation_message = Message("user", f"""For the {k+1}\'th step, You made the following operation:\nfunction_name: {operation.tool_name}\n{orjson.dumps(operation.tool_args).decode()}\nThen get the operation result:\n{operation.tool_output}\n""")
                additional_messages.append(operation_message)
            
            if is_modified:
                if self.config.enable_summary: 
                    new_message = summarize_plan(plan.to_json())
                else:
                    new_message = orjson.dumps(plan.to_json()).decode()
                new_message =  Message("user", f"""The plan after the {modify_steps}\'th step refinement is:\n{new_message}\n""")
            else:
                new_message = Message("user", f"The total plan stay unchanged")
            additional_messages.append(new_message)

                
            message,_ = self.plan_rectify_agent.parse(
                placeholders={
                    "system": {
                        "all_plan": orjson.dumps(task.plan.to_json()).decode(),
                        "refine_node_message": refine_node_message,
                        "workspace_files": file_archi,
                        "step_num": modify_steps,
                        "max_length": max_step,
                        "max_plan_tree_depth": self.config.max_plan_tree_depth,
                    },
                    "user": {
                        "subtask_id": plan.get_subtask_id(to_str=True),
                        "max_step": max_step,
                        "modify_steps": modify_steps,
                        "max_plan_tree_depth": self.config.max_plan_tree_depth,
                        "workspace_files": file_archi,
                        "refine_node_message":refine_node_message,
                    }
                },
                arguments=self.thought_arguments,
                functions=[self.plan_rectify_function], 
                function_call={'name':self.plan_rectify_function['name']},
                additional_messages=additional_messages,
                additional_insert_index=-1
            )

            tool_call = ToolCall()
            tool_call.set_tool(message['function_call']['name'],message['function_call']['arguments'])
            status_code,response = await self.execute(tool_call,
                                                      task.plan,
                                                      plan)
            
            operations.append(tool_call)
            recorder.regist_plan_modify(
                tool_call.tool_name,
                tool_call.tool_args,
                response,
                task.plan.to_json(posterior=True)
            )
            
            if status_code == PlanOperationStatusCode.MODIFY_SUCCESS:
                is_modified = True
            logger.typewriter_log("SYSTEM: ", Fore.YELLOW, response)
            logger.typewriter_log("PLAN MODIFY STATUS CODE: ",
                                  Fore.YELLOW, 
                                  f"{status_code.color()}{status_code.name}{Style.RESET_ALL}")
            
        logger.typewriter_log(
            f"-=-=-=-=-=-=-= REFINE PLAN EXITED -=-=-=-=-=-=-=",
            Fore.GREEN,
        )
        return task

    
    async def posterior_process(self, task:PlanExecutionNode, last_plan:Plan, tools_schema:list[dict])->Plan:
        logger.typewriter_log(
            f"-=-=-=-=-=-=-= POSTERIOR_PROCESS, working memory, summary, and reflection -=-=-=-=-=-=-=",
            Fore.BLUE,
        )
        
        all_plan = task.plan.to_json()
        terminal_plan = last_plan.to_json()
        action_process = [action.to_json() for action in task.actions]
        
        if self.config.enable_summary:
            all_plan = summarize_plan(all_plan)
            terminal_plan = summarize_plan(terminal_plan)
            action_process = summarize_action(action_process, terminal_plan)
        else:
            all_plan = orjson.dumps(all_plan).decode()
            terminal_plan = orjson.dumps(terminal_plan).decode()
            action_process = orjson.dumps(action_process).decode()

        message,_ = self.reflection_agent.parse(
            placeholders={
                "system": {
                    "all_plan": all_plan,
                    "terminal_plan": terminal_plan,
                    "tool_functions_description_list": orjson.dumps(tools_schema),
                    "action_process": action_process
                }
            },
            arguments=self.reflection_arguments
        )

        posterior_data = message["arguments"]
            

        summary = posterior_data["summary"]
        last_plan.data.action_list_summary = summary

        if "reflection_of_plan" in posterior_data.keys():
            last_plan.data.posterior_plan_reflection = posterior_data["reflection_of_plan"]

        if "reflection_of_tool" in posterior_data.keys():
            last_plan.data.tool_reflection = posterior_data["reflection_of_tool"]
            
        return last_plan