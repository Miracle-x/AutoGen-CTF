import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

import autogen
import chromadb
from qdrant_client import QdrantClient
from autogen import AssistantAgent
from autogen.agentchat.contrib.web_surfer import WebSurferAgent

from agents.attack_agent import AttackAgent
from agents.code_exec_agent import CodeExecAgent
from autogen.agentchat.contrib.qdrant_retrieve_user_proxy_agent import QdrantRetrieveUserProxyAgent
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

user_proxy = autogen.ConversableAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=llm_config
)

rag_assistant = QdrantRetrieveUserProxyAgent(
    name="rag_assistant",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    retrieve_config={
        "task": "qa",
        "docs_path": [
            "./all_prompt_db.txt",
        ],  
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": QdrantClient(":memory:"),
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "customized_prompt": """Find task from the Context. Tell me the task as it is and add the 'TERMINATE' after the answer. Just reply it.

Context is: {input_context}
"""
    },
    code_execution_config=False,
)

attack_assistant = AttackAgent(
    name="plan_assistant",
    llm_config=llm_config,
    agents=[rag_assistant]
)

task = """Tell me about http://47.251.44.45:40313."""

# 开始聊天
user_proxy.initiate_chat(
    recipient=attack_assistant,
    message=task,
    clear_history=False,
    request_reply=True
)