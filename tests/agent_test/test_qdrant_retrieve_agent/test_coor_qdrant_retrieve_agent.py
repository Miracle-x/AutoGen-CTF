import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

from qdrant_client import QdrantClient
import autogen
from agents.qdrant_retrieve_user_proxy_agent import QdrantRetrieveUserProxyAgent
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.retrieve_utils import TEXT_FORMATS
from typing import List, Dict, Optional

class CoorRetrieveGoodsAgent:
    def __init__(self, config_list: List[Dict], docs_paths: List[str], chunk_token_size: int = 2000, embedding_model: str = "BAAI/bge-small-en-v1.5"):
        self.config_list = config_list
        self.docs_paths = docs_paths
        self.chunk_token_size = chunk_token_size
        self.embedding_model = embedding_model
        
        assert len(self.config_list) > 0, "Config list is empty"
        print("models to use: ", [self.config_list[i]["model"] for i in range(len(self.config_list))])
        print("Accepted file formats for `docs_path`:")
        print(TEXT_FORMATS)
        
        # 创建 RetrieveAssistantAgent 实例
        self.assistant = RetrieveAssistantAgent(
            name="assistant",
            system_message="You are a helpful assistant.",
            llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "config_list": self.config_list,
            },
        )

        # 创建 QdrantRetrieveUserProxyAgent 实例
        self.ragproxyagent = QdrantRetrieveUserProxyAgent(
            name="ragproxyagent",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            retrieve_config={
                "task": "qa",
                "docs_path": self.docs_paths,
                "chunk_token_size": self.chunk_token_size,
                "model": self.config_list[0]["model"],
                "client": QdrantClient(":memory:"),
                "embedding_model": self.embedding_model,
            },
            code_execution_config=False,
        )

    def reset_assistant(self):
        self.assistant.reset()

    def initiate_retrieve_chat(self, problem: str):
        self.reset_assistant()
        self.ragproxyagent.initiate_chat(self.assistant, message=self.ragproxyagent.message_generator, problem=problem)
        return self.assistant.last_message()["content"]
        

if __name__ == '__main__':
    config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")

    # 配置文档路径
    docs_paths = [
        "./all_prompt_db.txt",
    ]

    # 创建 CoorRetrieveGoodsAgent 实例
    agent = CoorRetrieveGoodsAgent(config_list=config_list, docs_paths=docs_paths)

    # 执行检索任务
    qa_problem = "tell me somthing about http://43.136.237.143:40025"
    result = agent.initiate_retrieve_chat(problem=qa_problem)
    print(result)
