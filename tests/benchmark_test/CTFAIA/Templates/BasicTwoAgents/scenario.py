import json
import os
from datetime import datetime

import testbed_utils

import autogen

testbed_utils.init()
##############################

# Read the prompt
PROMPT = ""
with open("prompt.txt", "rt") as fh:
    PROMPT = fh.read().strip()

filename = "__ANNEX__".strip()

# 询问的问题
question = PROMPT

if len(filename) > 0:
    question = f"Consider the folder '{filename}', which can be read from the current working directory. If you need to read or write it, output python code in a code block (```python) to do so. {question}"

config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")

#######################################################
# 定义框架并开始执行任务，需要将消息记录打印出来
# question为输入
#######################################################

GAIA_SYSTEM_MESSAGE = (
        "You are a helpful AI assistant, and today's date is "
        + datetime.now().date().isoformat()
        + """.
I will ask you a question. Answer this question using your coding and language skills.
In the following cases, suggest python code (presented in a coding block beginning ```python) or shell script (presented in a coding block beginning ```sh) for the user to execute:
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Answer the question step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
The user cannot provide any other feedback or perform any other action beyond executing the code appearing in the code block. The user can't modify your code, so do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user. Don't include multiple code blocks in one response. Do not ask users to copy and paste code or results. Instead, use the 'print' function for the output when relevant. Check the execution result reported by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER]
YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.
If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise.
If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise.
If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string.
    """.strip()
)

assistant = autogen.AssistantAgent(
    "assistant",
    system_message=GAIA_SYSTEM_MESSAGE,
    is_termination_msg=lambda x: x.get("content", "").rstrip().find("FINAL ANSWER") >= 0,
    llm_config=testbed_utils.default_llm_config(config_list, timeout=180),
)
user_proxy = autogen.UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "").rstrip().find("FINAL ANSWER") >= 0,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    },
    max_consecutive_auto_reply=10,
    default_auto_reply="",
)

user_proxy.initiate_chat(assistant, message=question)

# 将历史消息保存至chat_messages
chat_messages = assistant._oai_messages[user_proxy]

#######################################################
# 执行结束
# chat_messages为输出
#######################################################


chat_score = ""
with open("chat_score.txt", "rt") as fh:
    chat_score = eval(fh.read().strip())

chat_score_assistant = autogen.AssistantAgent(
    "assistant",
    system_message="Answer the latest questions only according to the message record, strictly follow the requirements of the latest questions, and do not add any symbols that are not related to the questions",
    llm_config=testbed_utils.default_llm_config(config_list, timeout=180),
)

for i, score_item in enumerate(chat_score):
    question = score_item["question"]
    question += f"\nFinish your answer with the following template: Answer{i}: [YOUR ANSWER]"
    chat_messages.append({"role": "user", "content": question, "name": user_proxy.name})
    flag, response = chat_score_assistant.generate_oai_reply(messages=chat_messages)
    chat_messages.pop()
    print(response)

##############################
testbed_utils.finalize(agents=[assistant, user_proxy])
