import json
import os
import traceback

from colorama import Fore

from XAgentServer.envs import XAgentServerEnv
from XAgentServer.interaction import XAgentInteraction
from XAgentServer.loggers.logs import Logger
# from XAgentServer.manager import manager
from XAgentServer.response_body import WebsocketResponseBody


class XAgentServer:
    def __init__(self) -> None:
        self.logger: Logger = None

    def set_logger(self, logger):
        self.logger = logger

    async def interact(self, interaction: XAgentInteraction):
        # query = message
        
        from XAgent.config import CONFIG as config
        from XAgent.running_recorder import recorder
        from XAgent.tools import ToolServerInterface
        from XAgent.engines import PlanEngine,ReActEngine
        from XAgent.models import PlanExecutionNode,AutoGPTQuery
        # from XAgent.workflow.working_memory import WorkingMemoryAgent
        config.reload()
        # args
        args = interaction.parameter.args
        if interaction.base.recorder_root_dir:
            if not os.path.exists(interaction.base.recorder_root_dir):
                raise Exception(
                    f"recorder_root_dir {interaction.base.recorder_root_dir} not exists")
            recorder.load_from_disk(interaction.base.recorder_root_dir)
            query = recorder.get_query()
            self.logger.info(
                f"server is running, the start recorder_root_dir is {interaction.base.recorder_root_dir}")
        else:
            query = AutoGPTQuery(
                role_name=args.get('role_name', 'Assistant'),
                task=args.get('goal', ''),
                plan=args.get('plan', [
                ]),
            )
    
        self.logger.info(f"server is running, the start query is {args.get('goal', '')}")
        
        recorder.regist_query(query)
        recorder.regist_config(config)

        self.logger.info(json.dumps(config.to_dict(), indent=2))
        self.logger.typewriter_log(
            "Human-In-The-Loop",
            Fore.RED,
            str(config.enable_ask_human_for_help),
        )
        toolserver_if = ToolServerInterface()
        toolserver_if.lazy_init(config)

        # working memory function is used for communication between different agents that handle different subtasks
        # working_memory_function = WorkingMemoryAgent.get_working_memory_function()
        
        # subtask_functions, tool_functions_description_list = toolserver_if.get_available_tools()

        # all_functions = subtask_functions + working_memory_function


        upload_files = args.get("file_list", [])
        if upload_files is not None:
            upload_files = [os.path.join(XAgentServerEnv.Upload.upload_dir, interaction.base.user_id, file) for file in upload_files]
            for file_path in upload_files:
                try:
                    toolserver_if.upload_file(file_path)
                except Exception as e:
                    self.logger.typewriter_log(
                        "Error happens when uploading file",
                        Fore.RED,
                        f"{file_path}\n{e}",
                    )

        inital_node = PlanExecutionNode(
            role=args.get('role_name', 'Assistant'),
            task=args.get('goal', ''),
        )
        plan_engine = PlanEngine(config=config)
        execution_engine = ReActEngine(config=config)        
        
        try:
            self.logger.info(f"Start outer loop async")
            await plan_engine.run(inital_node,
                                  execution_engine=execution_engine,
                                  interaction=interaction)
        except Exception as e:
            self.logger.info(traceback.format_exc())
            raise e
        finally:
            toolserver_if.download_all_files()
            toolserver_if.close()