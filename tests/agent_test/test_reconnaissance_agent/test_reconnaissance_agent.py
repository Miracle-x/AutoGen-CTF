import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

import autogen
from agents.reconnaissance_agent import ReconnaissanceAgent

# 配置文件
config_list = [
    {
        "model": "gpt-4-turbo-preview",
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "base_url": os.environ.get("BASE_URL", "https://api.kwwai.top/v1")
    },
]
llm_config = {
    # "request_timeout": 600,
    "seed": 46,
    "config_list": config_list,
    "temperature": 0
}

# 代理设置
assistant = ReconnaissanceAgent(
    name="assistant",
    llm_config=llm_config,
    # return_mode="SIMPLE_CODE"
)

user_proxy = autogen.ConversableAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=llm_config
)

user_proxy.send(
    message="Reconnaissance http://47.251.44.45:40010",
    recipient=assistant,
    request_reply=True
)
