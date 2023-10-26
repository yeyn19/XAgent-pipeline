import os
import sys
import argparse
import json
import asyncio

from copy import deepcopy

from command import CommandLine,XAgentServerEnv
from XAgent.engines import PipelineV2Engine
# from XAgent.models.pipeline_automat import PipelineAutoMat
from XAgent.global_vars import reacttoolexecutor
from XAgent.config import CONFIG,ARGS

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str,
                        help="task description",required=True)
    parser.add_argument("--upload_files", nargs='+',
                        help="upload files")
    parser.add_argument("--model", type=str,)
    parser.add_argument("--record_dir", type=str,)
    parser.add_argument("--mode", type=str, default="auto",
                        help="mode, only support auto and manual, if you choose manual, you need to press enter to continue in each step")
    parser.add_argument("--quiet", action="store_true",default=False)
    
    parser.add_argument("--max_subtask_chain_length", type=int,)
    parser.add_argument("--enable_ask_human_for_help", action="store_true",)
    parser.add_argument("--max_plan_refine_chain_length", type=int,)
    parser.add_argument("--max_plan_tree_depth", type=int,)
    parser.add_argument("--max_plan_tree_width", type=int,)
    parser.add_argument("--max_retry_times", type=int,)
    parser.add_argument("--config_file",type=str,default=os.getenv('CONFIG_FILE', 'assets/config.yml'))

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    # CONFIG.reload(config_file="assets/private.yml")
    os.environ['CONFIG_FILE'] = "assets/private.yml"
    CONFIG.reload(config_file="assets/private.yml")

    # cmd = CommandLine(XAgentServerEnv)
    if args.quiet:
        original_stdout = sys.stdout
        from XAgent.running_recorder import recorder
        sys.stdout = open(os.path.join(recorder.record_root_dir,"command_line.ansi"),"w",encoding="utf-8")
    
    
    args = vars(args)
    
    for key,value in args.items():
        if value is not None:
            if key == 'model':
                ARGS['default_completion_kwargs'] = deepcopy(CONFIG['default_completion_kwargs'])
                ARGS['default_completion_kwargs']['model'] = value
            else:
                ARGS[key] = value

    reacttoolexecutor.lazy_init(CONFIG)
    reacttoolexecutor.get_available_tools()

    pipeline_engine = PipelineV2Engine(CONFIG)
    asyncio.run(pipeline_engine.run(pipeline_dir="assets/handcraft_pipelines/case1"))
    exit()
    
    cmd.start(
        args['task'],
        role="Assistant",
        mode=args['mode'],
        upload_files=args['upload_files'],
    )
    if args.quiet:
        sys.stdout.close()
        sys.stdout = original_stdout
    