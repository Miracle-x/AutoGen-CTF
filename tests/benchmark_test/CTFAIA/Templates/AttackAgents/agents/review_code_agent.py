import copy
import json
import requests
import re
from autogen import AssistantAgent, Agent, ConversableAgent, UserProxyAgent
from typing import Dict, Optional, Union, List, Tuple, Any, Literal


def remove_code_block_markers(input_text):
    # Remove ```json and ``` markers
    return re.sub(r'```json|```', '', input_text).strip()


def delete_empty_lines(text):
    return '\n'.join(line for line in text.splitlines() if line.strip())

expertise = """
1.Indicates that the localhost has 0.0.0.0, 127.0.0.1, localhost.
2.When the database compares strings, if the length of the two strings is different, a space is filled at the end of the shorter string to make the length of the two strings consistent.When data is inserted, if the data length exceeds the preset limit, the database truncates the string, retaining only the limited length.
3.If a web page uses' strcmp() 'for equality comparison, it can be passed to an array of' strcmp() 'functions instead of a string, which will output unexpected behavior that can be used to bypass conditional comparisons.
4.The md5 function cannot handle arrays and returns NULL if it is passed in as an array, so the encrypted value of both arrays is the same. You can bypass the strength comparison of the md5 function in this way. Use 'ffifdyop' to bypass queries such as "select * from 'admin' where password=md5($pass,true)".
5.When base64 decrypts a string, you can decrypt it three times and check whether the results of the three times are consistent, preventing an error when decrypting a string.
6.When you encounter a query similar to '$p3 === file_get_contents($p4) ', you can assign the p3 variable to 'php://input', assign a string to the variable p4, and post a string of the same value as the p4 assignment at the same time on the request, and pass it to p3 using a pseudo-protocol. To get around the comparison.
7.In SQL, semicolons are used to indicate the end of an sql statement. The end statement is followed by the next statement, which results in stack injection. Production scenario: mysql_multi_query() supports the execution of multiple sql statements at the same time.
8.If the response to different requests is the same or no response, then directly from the error injection, Boolean injection and delayed injection three methods to try,Otherwise, try joint injection or Stacked Queries Injection first.
"""

class ReviewCodeAgent(ConversableAgent):
    """
        Args:
            return_mode (str): 返回页面源代码，精简代码，还是页面源代码的总结.
                Possible values are “SIMPLE_CODE”, "SOURCE_CODE", "SUMMARY".
    """

    DEFAULT_PROMPT = (
        """You are a senior security expert, you can integrate the knowledge of CTF-Web direction, finding ideas for solving CTF challenges from the code""" + f"""Here are some expertise you might use:\n{expertise}"""
    )
    DEFAULT_DESCRIPTION = """An agent dedicated to code vulnerability analysis, which can complete the task of analyzing github code or historical message code. don't like tasks that have already been performed."""

    def __init__(
            self,
            name: str,
            description: Optional[str] = DEFAULT_DESCRIPTION,
            system_message: Optional[Union[str, List[str]]] = DEFAULT_PROMPT,
            llm_config: Optional[Union[Dict, Literal[False]]] = None,
            code_execution_config: Optional[str] = False,
            max_turns=3,
            **kwargs
    ):
        super().__init__(
            name=name,
            description=description or self.DEFAULT_DESCRIPTION,
            system_message=system_message or self.DEFAULT_PROMPT,
            llm_config=llm_config,
            **kwargs
        )
        self.max_turns = max_turns
        self.register_reply(Agent, ReviewCodeAgent._generate_review_code_reply)
        self._code_execution_config = code_execution_config

    def _generate_review_code_reply(
            self,
            messages: Optional[List[Dict]] = None,
            sender: Optional[Agent] = None,
            config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        if config is None:
            config = self
        if messages is None:
            messages = self._oai_messages[sender]
        # message = messages[-1]

        # Work with a copy of the messages
        _messages = copy.deepcopy(messages)

        # 当出现异常的时候立即continue重新进入循环执行
        error_times = 0
        while True:
            print('start', error_times)
            error_times += 1
            if error_times > self.max_turns:
                return True, "Failed to execute task"
            print('find code')
            # 根据历史消息判断要审阅的代码来源
            source_res = {}
            while True:
                extract_target_prompt = f"""Consider the following important questions:

                - Does the code you want to review come from github? What is the url detail?
                - Whether the code you want to review exists in the history message? Extract the complete code detail if yes.

                Please output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON, DO NOT USE CODE BLOCK, AND DO NOT DEVIATE FROM THIS SCHEMA:

                    {{
                        "source": {{
                            "detail": string,
                            "answer": string, (select from `history`,`github`)
                        }},
                    }}
                """
                _messages.append({"role": "user", "content": extract_target_prompt, "name": sender.name})
                response = self.client.create(
                    messages=_messages,
                    cache=self.client_cache,
                    # response_format={"type": "json_object"},
                )
                _messages.pop()
                extracted_response = self.client.extract_text_or_completion_object(response)[0]
                try:
                    extracted_response = remove_code_block_markers(extracted_response)
                    source_res = json.loads(extracted_response)
                except json.decoder.JSONDecodeError as e:
                    # Something went wrong. Restart this loop.
                    self._print_thought(str(e))
                    continue
                break
            print(source_res)

            # 获取代码
            code = ""
            if source_res['source']['answer'] == 'github':
                request_github = 0
                while request_github < 3:
                    request_github += 1
                    get_code_prompt = f"""Consider the following important questions:

                    - Url is {source_res['source']['detail']}. Is it a folder or a file?
                    - Whether the details of the files in this folder can be obtained by using api.github.com, and whether the file contents can be obtained by accessing a link.

                    write code in the following block to get complete file content

                    ```python
                    your code
                    ```

                    Only reply code block
                    """.strip()
                    _messages.append({"role": "user", "content": get_code_prompt, "name": sender.name})
                    response = self.client.create(
                        messages=_messages,
                        cache=self.client_cache,
                    )
                    _messages.pop()
                    extracted_response = self.client.extract_text_or_completion_object(response)[0]
                    # 打印获取源码的代码块
                    print('=================去获取源码的代码块===================')
                    print(extracted_response)
                    _messages.append({"role": "user", "content": extracted_response, "name": 'Programmer'})
                    flag, code = self.generate_code_execution_reply(messages=_messages,
                                                                    config=self._code_execution_config)
                    # print(code)
                    _messages.append({"role": "user", "content": code, "name": 'exec_result'})
                    # 检查代码是否有误
                    data = {}
                    while True:
                        check_prompt = f"""
                        Please output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON, AND DO NOT DEVIATE FROM THIS SCHEMA:

                        {{
                            "code_wrong": {{
                                "reason": string,
                                "answer": boolean(true or false)(true when need to fix the code bug)
                            }}
                        }}
                        """.strip()
                        _messages.append({"role": "user", "content": check_prompt, "name": sender.name})
                        response = self.client.create(
                            messages=_messages,
                            cache=self.client_cache,
                            # response_format={"type": "json_object"},
                        )
                        _messages.pop()
                        extracted_response = self.client.extract_text_or_completion_object(response)[0]
                        print(extracted_response)
                        try:
                            extracted_response = remove_code_block_markers(extracted_response)
                            data = json.loads(extracted_response)
                        except json.decoder.JSONDecodeError as e:
                            print(e)
                            continue
                        break
                    print('=================检查代码执行报错===================')
                    if data['code_wrong']['answer']:
                        print('aaa')
                        continue
                    else:
                        _messages.pop()
                        _messages.pop()
                        break
                if request_github >= 3:
                    return True, "Can't get the github code."
            elif source_res['source']['answer'] == 'history':
                code = source_res['source']['detail']
            print(code)

            # 审阅代码
            review_prompt = f"""Here is the code:
            
            {code}
            
            the request is:
            
            {messages[-1]['content']}
            
            Consider the following important questions:
            - Is there any mention of potential vulnerabilities in history, First look for evidence of their existence in the code!
            - Carefully analyze the constraints and logical relationships in the code, What are the clearly exploitable vulnerabilities? 
            - Find all code evidence of vulnerabilities, such as database field length limits, unsafe SQL commands.
            - How to tectonic attack code to exploit vulnerabilities(Need to have complete steps).
            
            Reply in the following format and sort by credibility(Only the Vulnerability already in the code. Don't list vulnerabilities without evidence):
            
            # (answer of the request)
            
            1. Vulnerability type
            
                **Vulnerability description**:
                (text)
            
                **source code**: 
                (complete Core Code not text)
                
                **attack code**:
                (text)
            
            2. ···
            """.strip()
            _messages.append({"role": "user", "content": review_prompt, "name": sender.name})
            flag, extracted_response = self.generate_oai_reply(messages=_messages)
            # print(extracted_response)

            return flag, extracted_response
