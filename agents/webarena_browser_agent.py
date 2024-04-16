import copy

import markdownify
from autogen import Agent, ConversableAgent
from typing import Dict, Optional, Union, List, Tuple, Any, Literal

import argparse
import logging
import os
import random
import time

from bs4 import BeautifulSoup

from agent import (
    construct_agent,
)
from agent.prompts import *
from browser_env import (
    ScriptBrowserEnv,
)
from browser_env.auto_login import get_site_comb_from_filepath
from browser_env.helper_functions import (
    RenderHelper,
)
from evaluation_harness import evaluator_router
from webarena_agents import ActionTakingCapability, EnvironmentAgent

import autogen

LOG_FOLDER = "log_files"
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
LOG_FILE_NAME = f"{LOG_FOLDER}/log_{time.strftime('%Y%m%d%H%M%S', time.localtime())}_{random.randint(0, 10000)}.log"

logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE_NAME)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Set the log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)


def delete_empty_lines(text):
    return '\n'.join(line for line in text.splitlines() if line.strip())


def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run end-to-end evaluation on the benchmark")
    parser.add_argument("--render", action="store_true", help="Render the browser")
    parser.add_argument(
        "--slow_mo",
        type=int,
        default=0,
        help="Slow down the browser by the specified amount",
    )
    parser.add_argument("--action_set_tag", default="id_accessibility_tree", help="Action type")
    parser.add_argument(
        "--observation_type",
        choices=["accessibility_tree", "html", "image"],
        default="accessibility_tree",
        help="Observation type",
    )
    parser.add_argument(
        "--current_viewport_only",
        action="store_true",
        help="Only use the current viewport for the observation",
    )
    parser.add_argument("--viewport_width", type=int, default=1280)
    parser.add_argument("--viewport_height", type=int, default=720)
    parser.add_argument("--save_trace_enabled", action="store_true")
    parser.add_argument("--sleep_after_execution", type=float, default=0.0)

    parser.add_argument("--max_steps", type=int, default=30)

    # agent config
    parser.add_argument("--agent_type", type=str, default="prompt")
    parser.add_argument(
        "--instruction_path",
        type=str,
        default="p_cot_id_actree_2s.json",
    )
    parser.add_argument(
        "--parsing_failure_th",
        help="When concesecutive parsing failure exceeds this threshold, the agent will stop",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--repeating_action_failure_th",
        help="When concesecutive repeating action exceeds this threshold, the agent will stop",
        type=int,
        default=3,
    )

    # lm config
    parser.add_argument("--provider", type=str, default="openai")
    parser.add_argument("--model", type=str, default="gpt-4")
    parser.add_argument("--mode", type=str, default="chat")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--context_length", type=int, default=0)
    parser.add_argument("--max_tokens", type=int, default=384)
    parser.add_argument("--stop_token", type=str, default=None)
    parser.add_argument(
        "--max_retry",
        type=int,
        help="max retry times to perform generations when parsing fails",
        default=1,
    )
    parser.add_argument(
        "--max_obs_length",
        type=int,
        help="when not zero, will truncate the observation to this length before feeding to the model",
        default=1920,
    )
    parser.add_argument(
        "--model_endpoint",
        help="huggingface model endpoint",
        type=str,
        default="",
    )

    # example config
    parser.add_argument("--test_start_idx", type=int, default=1)
    parser.add_argument("--test_end_idx", type=int, default=2)

    # logging related
    parser.add_argument("--result_dir", type=str, default="myresultdir_debug")
    args = parser.parse_args()

    # check the whether the action space is compatible with the observation space
    if args.action_set_tag == "id_accessibility_tree" and args.observation_type != "accessibility_tree":
        raise ValueError(
            f"Action type {args.action_set_tag} is incompatible with the observation type {args.observation_type}"
        )

    return args


def prepare(args: argparse.Namespace) -> None:
    # prepare result dir
    result_dir = args.result_dir
    if not result_dir:
        result_dir = f"cache/results_{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
    if not Path(result_dir).exists():
        Path(result_dir).mkdir(parents=True, exist_ok=True)
        args.result_dir = result_dir
        logger.info(f"Create result dir: {result_dir}")

    if not (Path(result_dir) / "traces").exists():
        (Path(result_dir) / "traces").mkdir(parents=True)

    # if not (Path(result_dir) / "storage_state.json").exists():
    #     with open(os.path.join(result_dir, "storage_state.json"), "a") as file:
    #         file.write("{}")

    # log the log file
    with open(os.path.join(result_dir, "log_files.txt"), "a+") as f:
        f.write(f"{LOG_FILE_NAME}\n")


def dump_config(args: argparse.Namespace) -> None:
    config_file = Path(args.result_dir) / "config.json"
    if not config_file.exists():
        with open(config_file, "w") as f:
            json.dump(vars(args), f, indent=4)
            logger.info(f"Dump config to {config_file}")


def HTML2Markdown(html):
    soup = BeautifulSoup(html, "html.parser")
    webpage_text = markdownify.MarkdownConverter().convert_soup(soup)
    webpage_text = re.sub(r"\r\n", "\n", webpage_text)
    webpage_text = re.sub(r"\n{2,}", "\n\n", webpage_text).strip()
    return webpage_text


class WebarenaBrowserAgent(ConversableAgent):
    """
        Args:
    """

    DEFAULT_PROMPT = (
        """You are a helpful assistant."""
    )
    DEFAULT_DESCRIPTION = """A helpful assistant who can use browser according to instructions."""

    def __init__(
            self,
            name: str,
            description: Optional[str] = DEFAULT_DESCRIPTION,
            system_message: Optional[Union[str, List[str]]] = DEFAULT_PROMPT,
            llm_config: Optional[Union[Dict, Literal[False]]] = None,
            render: Optional[bool] = True,
            observation_type: Optional[str] = "accessibility_tree",
            instruction_path: Optional[str] = "p_cot_id_actree_2s.json",
            **kwargs
    ):
        super().__init__(
            name=name,
            description=description or self.DEFAULT_DESCRIPTION,
            system_message=system_message or self.DEFAULT_PROMPT,
            llm_config=llm_config,
            **kwargs
        )
        args = config()
        args.render = render
        args.observation_type = observation_type
        args.instruction_path = instruction_path
        args.sleep_after_execution = 2.0
        # 创建输出文件
        prepare(args)
        # 保存参数
        dump_config(args)
        # promptAgent
        agent = construct_agent(args)
        # 提前停止条件
        early_stop_thresholds = {
            "parsing_failure": args.parsing_failure_th,
            "repeating_action": args.repeating_action_failure_th,
        }
        # 参数
        self.args = args
        # 等第一次接受到url时再初始化浏览器环境
        self.env_agent = None
        # 动作指导Assistant
        self.action_agent = autogen.AssistantAgent(
            "action_agent",
            llm_config=llm_config,
            system_message="",
        )
        action_taking_capability = ActionTakingCapability(
            prompt_constructor=agent.prompt_constructor,
            action_set_tag=args.action_set_tag,
            max_steps=args.max_steps,
            early_stop_thresholds=early_stop_thresholds,
        )
        action_taking_capability.add_to_agent(self.action_agent)
        self.register_reply(Agent, WebarenaBrowserAgent._generate_browser_reply)

    def _init_env_agent(
            self,
            start_url,
            intent,
    ):
        args = self.args
        # 任务配置
        task_config = {
            "task_id": 1,
            "require_login": False,
            # "storage_state": f"{args.result_dir}/storage_state.json",
            "storage_state": None,
            "start_url": start_url,
            "geolocation": None,
            "intent_template": "tell me all subreddits starting with character '{{character}}'",
            "instantiation_dict": {"character": "a"},
            "intent": intent,
            "require_reset": False,
            "eval": {
                "eval_types": ["string_match"],
                "reference_answers": ["announcements Art AskReddit askscience aww"],
                "reference_url": "",
                "program_html": [
                    {
                        "url": "",
                        "required_contents": []
                    }
                ]
            },
            "reference_action_sequence": {
                "action_set_tag": "playwright",
                "action_sequence": [
                    "page.get_by_role(\"link\", name=\"Forums\").click()",
                    "page.get_by_role(\"link\", name=\"Alphabetical\").click()",
                    "page.stop(\"announcements Art AskReddit askscience aww\")"
                ]
            }
        }
        config_file_path = f"{args.result_dir}/task_config.json"
        with open(config_file_path, "w") as f:
            json.dump(task_config, f)
        # web环境
        env = ScriptBrowserEnv(
            headless=not args.render,
            slow_mo=args.slow_mo,
            observation_type=args.observation_type,
            current_viewport_only=args.current_viewport_only,
            viewport_size={
                "width": args.viewport_width,
                "height": args.viewport_height,
            },
            save_trace_enabled=args.save_trace_enabled,
            sleep_after_execution=args.sleep_after_execution,
        )
        # 环境agent
        self.env_agent = EnvironmentAgent(
            name="env_agent",
            env=env,
            config_file=config_file_path,
            result_dir=args.result_dir,
            action_set_tag=args.action_set_tag,
            llm_config=False,
            code_execution_config=False,
        )

    def _generate_browser_reply(
            self,
            messages: Optional[List[Dict]] = None,
            sender: Optional[Agent] = None,
            config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        if config is None:
            config = self
        if messages is None:
            messages = self._oai_messages[sender]
        message = messages[-1]

        # Work with a copy of the messages
        _messages = copy.deepcopy(messages)

        # 当出现异常的时候立即continue重新进入循环执行
        error_times = 0
        while True:
            error_times += 1
            if error_times > 3:
                return False, None
            # 提取初始化的url
            extract_url_prompt = """Extract the url to be accessed and return only the url. DO NOT OUTPUT ANYTHING OTHER THAN url."""
            _messages.append({"role": "user", "content": extract_url_prompt, "name": sender.name})
            response = self.client.create(
                messages=_messages,
                cache=self.client_cache,
            )
            _messages.pop()
            start_url = self.client.extract_text_or_completion_object(response)[0]
            print('*' * 10 + '目标初始url' + '*' * 10)
            print(start_url)

            if not self.env_agent:
                self._init_env_agent(start_url, intent=message)

            chat = self.env_agent.initiate_chat(
                message={
                    "content": {"intent": message},
                },
                recipient=self.action_agent,
                request_reply=True
            )
            answer = chat.chat_history[-1]['context']['trajectory'][-1]['answer']
            # last_obs是可访问树，暂时不需要
            # last_obs = chat.chat_history[-1]['context']['state_info']['observation']['text']
            last_page_url = chat.chat_history[-1]['context']['state_info']['info']['page'].url
            last_page_content = chat.chat_history[-1]['context']['state_info']['info']['page'].content
            last_page_markdown = HTML2Markdown(last_page_content)
            result = f"""We operate the browser according to the instructions and get the following answer:
{answer}  
     
The final html of the browser is as follows:
URL: {last_page_url}
{last_page_markdown}
            """
            return True, result
