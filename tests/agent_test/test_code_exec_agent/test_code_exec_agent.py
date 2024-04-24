import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

import autogen

from agents.code_exec_agent import CodeExecAgent

task = """Visit the URL http://47.251.44.45:40010. And find the flag."""
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

code_exec_agent = CodeExecAgent(
    name="code_exec_agent",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
)
user_proxy = autogen.ConversableAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=llm_config
)

user_proxy.initiate_chat(
    recipient=code_exec_agent,
    message=task,
    clear_history=False,
    request_reply=True
)
