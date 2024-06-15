import copy
import json
import requests
import re
from autogen import AssistantAgent, Agent, ConversableAgent, UserProxyAgent
from typing import Dict, Optional, Union, List, Tuple, Any, Literal
from bs4 import BeautifulSoup
from autogen.agentchat.contrib.text_analyzer_agent import TextAnalyzerAgent


def remove_code_block_markers(input_text):
    # Remove ```json and ``` markers
    # input_text = re.sub(r'```json|```', '', input_text).strip()
    pattern = r'\{.*\}'
    match = re.search(pattern, input_text, re.DOTALL)
    if match:
        return match.group(0)
    else:
        exit()


def delete_empty_lines(text):
    return '\n'.join(line for line in text.splitlines() if line.strip())


def filter_html(html_source):
    # 解析HTML源码
    soup = BeautifulSoup(html_source, 'html.parser')

    # 保留的标签列表
    keep_tags = {
        'input', 'button', 'select', 'textarea', 'form', 'label',
        'fieldset', 'legend', 'datalist', 'optgroup', 'option',
        'img', 'audio', 'video', 'source', 'track', 'a', 'script',
        'meta', 'link', 'iframe', 'object', 'embed', 'param', 'noscript', 'base'
    }

    # 遍历文档树并过滤标签
    for tag in soup.find_all(True):
        if tag.name == 'style':
            # 移除 style 标签及其内容
            tag.decompose()
        elif tag.name not in keep_tags:
            # 替换标签但保留其内部内容
            tag.unwrap()

    return delete_empty_lines(str(soup))


class ReconnaissanceAgent(ConversableAgent):
    """
        Args:
            return_mode (str): 返回页面源代码，精简代码，还是页面源代码的总结.
                Possible values are “SIMPLE_CODE”, "SOURCE_CODE", "SUMMARY".
    """

    DEFAULT_PROMPT = (
        """You are a helpful assistant."""
    )
    DEFAULT_DESCRIPTION = """A TOOL to reconnaissance target url. Return the source code of the relevant pages of the same station. The same url will give exactly the same answer to avoid repeating the url before investigation."""

    def __init__(
            self,
            name: str,
            description: Optional[str] = DEFAULT_DESCRIPTION,
            system_message: Optional[Union[str, List[str]]] = DEFAULT_PROMPT,
            llm_config: Optional[Union[Dict, Literal[False]]] = None,
            return_mode: Optional[str] = "SOURCE_CODE",
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
        self.return_mode = return_mode
        self.analyzer = TextAnalyzerAgent(llm_config=llm_config)
        self.register_reply(Agent, ReconnaissanceAgent._generate_reconnaissance_reply)
        self.max_turns = max_turns
        self.urls = []

    def _generate_reconnaissance_reply(
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
            error_times += 1
            if error_times > self.max_turns:
                return False, None
            # 提取初始化的url
            extract_url_prompt = """Only extract the target URL and return it. DO NOT OUTPUT ANYTHING OTHER THAN THE URL. Don't explain and illustrate. Only URL!"""
            _messages.append({"role": "user", "content": extract_url_prompt, "name": sender.name})
            response = self.client.create(
                messages=_messages,
                cache=self.client_cache,
            )
            _messages.pop()
            start_url = self.client.extract_text_or_completion_object(response)[0]
            print('*' * 10 + '目标初始url' + '*' * 10)
            print(start_url)

            # 访问初始化url页面
            try:
                start_url_response = requests.get(start_url)
                start_url_response = 'Header:\n' + str(
                    start_url_response.headers) + '\n\nContent:\n' + start_url_response.text
                start_url_response = delete_empty_lines(start_url_response)
            except:
                continue
            print('*' * 10 + '目标初始页面' + '*' * 10)
            print(start_url_response)

            # 分析页面是否有更多的相关页面 提取对当前任务有帮助的url
            analyse_more_page_prompt = f"""Extract urls that is helpful for the current request in the current page as a list. Note that the url must be complete.
Extract some important url like main.js admin.php
Ignore unimportant url such as. css .jpg .png base64-image .mp4 .mp3
        
Current request: {messages[-1].get('content')}
            
Current Page:
url:{start_url}
source_code:
{start_url_response}

Please output an answer in pure JSON format according to the following schema. The JSON object must be parsable as-is. DO NOT OUTPUT ANYTHING OTHER THAN JSON, DO NOT USE CODE BLOCK, AND DO NOT DEVIATE FROM THIS SCHEMA:
{{
    "list": list[string]
}}
"""
            _messages.append({"role": "user", "content": analyse_more_page_prompt, "name": sender.name})
            response = self.client.create(
                messages=_messages,
                cache=self.client_cache,
                # response_format={"type": "json_object"},
            )
            _messages.pop()
            extracted_response = self.client.extract_text_or_completion_object(response)[0]
            relate_urls = None
            try:
                extracted_response = remove_code_block_markers(extracted_response)
                relate_urls = json.loads(extracted_response)
            except json.decoder.JSONDecodeError as e:
                print(str(e))
                continue
            print('*' * 10 + '同站相关url' + '*' * 10)
            print(relate_urls['list'])

            relate_pages = {}
            try:
                for url in relate_urls['list']:
                    if not url:
                        continue
                    tmp_response = requests.get(url)
                    tmp_response = 'Header:\n' + str(tmp_response.headers) + '\n\nContent:\n' + tmp_response.text
                    tmp_response = delete_empty_lines(tmp_response)
                    relate_pages[url] = tmp_response
            except:
                continue
            # print('*' * 10 + '同站相关页面' + '*' * 10)
            # print(relate_pages)

            result = relate_pages
            result[start_url] = start_url_response

            if self.return_mode == "SUMMARY":
                summary_prompt = """Summarize the page and explain the function of each part of the page without code, as concise as possible."""
                for url, text in result.items():
                    result[url] = self.analyzer.analyze_text(text, summary_prompt)
            elif self.return_mode == "SIMPLE_CODE":
                for url, text in result.items():
                    result[url] = filter_html(text)

            for url, text in result.items():
                if len(text) > 10000:
                    result[url] = f"The length of this page is {len(text)}. It is to long, don't visit"

            return True, json.dumps(result, ensure_ascii=False)
