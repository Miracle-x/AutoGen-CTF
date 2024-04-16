import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

from agents.webarena_browser_agent import WebarenaBrowserAgent
import autogen

config_list = [
    {
        "model": "gpt-4-turbo-preview",
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "base_url": os.environ.get("BASE_URL", "https://api.kwwai.top/v1")
    },
]
llm_config = {
    # "request_timeout": 600,
    "seed": 45,
    "config_list": config_list,
    "temperature": 0
}

browser_agent_instruction_path = 'p_cot_id_actree_2s.json'
browser_agent = WebarenaBrowserAgent(
    "browser_agent",
    observation_type="accessibility_tree",  # choices=["accessibility_tree", "html", "image"]
    instruction_path=browser_agent_instruction_path,
    llm_config=llm_config
)

user_proxy = autogen.ConversableAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=llm_config
)

task = [
    "the target url is http://metis.lti.cs.cmu.edu:9999/. tell me all subreddits starting with character 'a'",
    "Visit the URL http://43.136.237.143:40033/. And add a random product. ",
    "visit https://baidu.com and search the info about sql-lab less-1 solution"
]

user_proxy.send(
    message=task[0],
    recipient=browser_agent,
    request_reply=True
)
