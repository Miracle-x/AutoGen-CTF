运行在python3.10环境

执行以下代码安装webarena库

```
pip install -e ./package_source/webarena
pip install --upgrade pyautogen
```

使用下面的命令设置环境变量(windows)
<api_key>,<base_url>需要使用自己的，不需要base_url可不设置

```
set OPENAI_API_KEY=<api_key>
set BASE_URL=<base_url>
```

设置完可以执行main文件检查一下是否成功



使用以下文件测试浏览器agent

```
cd tests/agent_test/test_webarena_browser_agent
python test_webarena_browser_agent.py
```


