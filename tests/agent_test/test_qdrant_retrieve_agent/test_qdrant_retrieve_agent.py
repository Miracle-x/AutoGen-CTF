import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

from qdrant_client import QdrantClient
import autogen
from agents.qdrant_retrieve_agent import CoorRetrieveGoodsAgent
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent

# Accepted file formats for that can be stored in
# a vector database instance
from autogen.retrieve_utils import TEXT_FORMATS

config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")

# 1. create a RetrieveAssistantAgent instance named "assistant"
assistant = RetrieveAssistantAgent(
    name="assistant",
    system_message="You are a helpful assistant.",
    llm_config={
        "timeout": 600,
        "cache_seed": 42,
        "config_list": config_list,
    },
)

# 2. create the QdrantRetrieveUserProxyAgent instance named "ragproxyagent"
ragproxyagent = CoorRetrieveGoodsAgent(
    name="ragproxyagent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    retrieve_config={
        "task": "code",
        "docs_path": [
            "https://raw.githubusercontent.com/microsoft/flaml/main/README.md",
            "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Research.md",
        ],  # change this to your own path, such as https://raw.githubusercontent.com/microsoft/autogen/main/README.md
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": QdrantClient(":memory:"),
        "embedding_model": "BAAI/bge-small-en-v1.5",
    },
    code_execution_config=False,
)

# reset the assistant. Always reset the assistant before starting a new conversation.
assistant.reset()

qa_problem = "Is there a function called tune_automl?"
ragproxyagent.initiate_chat(assistant, message=ragproxyagent.message_generator, problem=qa_problem)
