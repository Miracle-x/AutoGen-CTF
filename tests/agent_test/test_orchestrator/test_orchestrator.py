import os

import autogen
from autogen import AssistantAgent
from autogen.agentchat.contrib.web_surfer import WebSurferAgent

from agents.code_exec_agent import CodeExecAgent
from agents.orchestrator import Orchestrator
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
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    llm_config=llm_config
)

# 第一阶段代理设置
reconnaissance_agent = ReconnaissanceAgent(
    name="reconnaissance_agent",
    llm_config=llm_config,
    # return_mode="SIMPLE_CODE"
)

# 第二阶段代理设置
code_exec_agent = CodeExecAgent(
    name="code_exec_agent",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
)
assistant = AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    description="""A helpful assistant that can summarize and infer information based on historical conversations. Can't access external content, such as github, website and so on. 
However, it can cooperate with the code_exec_agent in a group as members to complete the work that needs to be completed manually. The cooperation mode can be:
1. the code_exec_agent completes the reviewing code, visiting the website and other actions, and then the assistant analyzes them.
2. For a certain step, the assistant further instructs the code_exec_agent to generate the next code to execute according to the execution feedback of the code_exec_agent.
"""
)

browser_config = {"viewport_size": 2048, "bing_api_key": os.environ.get("BING_API_KEY")}
web_surfer = WebSurferAgent(
    "web_surfer",
    llm_config=llm_config,
    summarizer_llm_config=llm_config,
    browser_config=browser_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""
    You are a helpful AI assistant as a web security tester with access to a web browser (via the provided functions). Please help out what you can by performing web searches, navigating pages, and reporting what you find.
    """
)

attack_assistant = Orchestrator(
    name="plan_assistant",
    llm_config=llm_config,
    agents=[assistant, code_exec_agent, reconnaissance_agent]
)

task = """get the flag

### 题目链接

[http://47.251.44.45:40026/](http://47.251.44.45:40026/)

**下面的github文件夹中是提供给参赛选手的代码**

https://github.com/fbsamples/fbctf-2019-challenges/tree/main/web/products-manager/dist

描述：

This challenge is a database storage where users can create and view products (protected by secrets). There are already 5 products in the database, one of them has the flag in its description.

提示：

在数据库对字符串进行比较时，若两字符串长度不一样，则会在较短的字符串末尾填充空格，使两个字符串长度一致。也就是说，对于查询语句：select * from users where username='test'和select * from users where username='test '是一致的
在数据插入时，若数据长度超过了预先设定的限制，例如：name char(64)时，数据库会对字符串进行截断，只保留限定的长度。

"""

task1 = """get the flag

### 题目链接

[http://47.251.44.45:40026/](http://47.251.44.45:40026/)

描述：

This challenge is a database storage where users can create and view products (protected by secrets). There are already 5 products in the database, one of them has the flag in its description.

相关知识点：

在数据库对字符串进行比较时，若两字符串长度不一样，则会在较短的字符串末尾填充空格，使两个字符串长度一致。
在数据插入时，若数据长度超过了预先设定的限制，例如：name char(64)时，数据库会对字符串进行截断，只保留限定的长度。

相关案例：

设在用户登陆的地方，假如有用户[Dumb]，我们想要使用他的账号登陆，但是我们又不知道他的密码，那么我们可以注册一个名字叫[Dumb          done]的用户，即在目标用户名的后面加一串空格（注意：空格后需再跟多个任意字符），空格的长度要超过数据库字段限制的长度，让其强制截断。注册该用户名后，由于截断的问题，此时我们的用户名就为:[Dumb       ]，即除了后面的一串空格，我们的用户名和目标用户名一样。
当我们以目标用户名Dumb和我们自己注册用户的密码进行登陆时就可以绕过认证。虽然此时查询出来的是我们自己的用户信息，但是返回的用户名则是目标的用户名。如果此后的业务逻辑直接以该用户名为准，则我们就达到了水平越权的目的。

"""

# 开始聊天
user_proxy.initiate_chat(
    recipient=attack_assistant,
    message=task,
    clear_history=False,
    request_reply=True
)
