运行在python3.10环境

执行以下代码安装webarena库

```
pip install -e ./package_source/webarena
pip install --upgrade pyautogen
```

使用下面的命令设置环境变量(windows)
<name>需要使用自己的，不需要base_url可不设置<base_url>
OAI_CONFIG_LIST里的内容需要更新成自己的配置

```
export OPENAI_API_KEY=<openai_api_key>
export BASE_URL=<base_url>
export HUGGINGFACE_API_KEY=<huggingface_api_key>
export OAI_CONFIG_LIST=$(cat ./OAI_CONFIG_LIST)
```



使用以下文件测试浏览器agent

```
cd tests/agent_test/test_webarena_browser_agent
python test_webarena_browser_agent.py
```


