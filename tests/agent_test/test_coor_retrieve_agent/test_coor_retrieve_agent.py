import os
import autogen
import chromadb
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent

from agents.coor_retrieve_agent import CoorRetrieveGoodsAgent

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

retrieve_config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "base_url": os.environ.get("BASE_URL", "https://api.kwwai.top/v1")
    },
]
retrieve_llm_config = {
    # "request_timeout": 600,
    "seed": 52,
    "config_list": retrieve_config_list,
    "temperature": 0
}

retrieve_config = {
    "task": "qa",
    "docs_path": "./all_prompt_db.txt",
    "chunk_token_size": 550,
    "model": llm_config["config_list"][0]["model"],
    "client": chromadb.PersistentClient(path="/tmp/chromadb"),
    "collection_name": "all_prompt_db",
    "chunk_mode": "multi_lines",
    "must_break_at_empty_line": True,
    "get_or_create": True,
}

rag_assistant = CoorRetrieveGoodsAgent(
    name="rag_assistant",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    human_input_mode="NEVER",
    llm_config=retrieve_llm_config,
    retrieve_config=retrieve_config,
    code_execution_config=False,  # we don't want to execute code in this case.
    description="Assistant who has extra content retrieval power for solving difficult problems.",
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
    message="tell me somthing about http://43.136.237.143:40025",
    recipient=rag_assistant,
    request_reply=True
)


