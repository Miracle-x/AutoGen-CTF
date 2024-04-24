阿里巴巴国际站与西北工业大学联合开发项目

网络空间安全学院-NLP&大模型安全课题组-高德宏&杨黎斌&刘鹏望&胥基&赖起敬&张一涵&周梓伦

[**[LeaderBoard]**](https://huggingface.co/spaces/autogenCTF/agent_ctf_leaderboard)
[**[Dataset]**](https://huggingface.co/datasets/autogenCTF/CTFAIA)
[**[CTF platform]**](http://47.251.44.45:8000)
[**[GitHub]**](https://github.com/Miracle-x/AutoGen-CTF)


## 基础库安装

运行在python3.10环境, 执行以下代码安装基本的依赖库

```shell
pip install -r requirements.txt
```

## 环境变量

使用下面的命令设置环境变量(bash)<br/>
其中"<...>"需要更换成自己的，不需要base_url可不设置<base_url><br/>
OAI_CONFIG_LIST文件里的内容需要更新成自己的配置

```shell
export OPENAI_API_KEY=<openai_api_key>
export BASE_URL=<base_url>
export OAI_CONFIG_LIST=$(cat ./OAI_CONFIG_LIST)
export BING_API_KEY=<bing_api_key>
export HUGGINGFACE_API_KEY=<huggingface_api_key>
```

## 单个agent测试

实际操作浏览器的agent, 这个需要额外安装一些依赖

```shell
pip install -r package_source/webarena/requirements.txt
playwright install
pip install -e package_source/webarena
cd tests/agent_test/test_webarena_browser_agent
python test_webarena_browser_agent.py
```

其他agent都是进入该测试目录直接执行就行<br/>
例如代码执行agent

```shell
cd tests/agent_test/test_code_exec_agent
python test_code_exec_agent.py
```

(由于版本更新，rag_assistant似乎不能用了，所有用到rag的agent都收到影响，正在重构中)

## benchmark测试

我们的基准测试基于autogenbench，此处只做本项目测评数据集的使用步骤，autogenbench的详细使用请参照 https://github.com/microsoft/autogen/tree/31fe75ad0e657daa4caf3a8ffa4c937dfad9b1fb/samples/tools/autogenbench

1. 安装相关库

```shell
pip install autogenbench
```

2. **如果是Windows系统，请确保docker已安装**，安装参考 https://www.docker.com/products/docker-desktop/

3. 进入要测试的数据集文件夹，以CTFAIA为例

```shell
cd tests/benchmark_test/CTFAIA
```

4. 运行初始化脚本 init_tasks.py
```shell
python Scripts/init_tasks.py
```

5. 运行一个任务，此处以**使用BasicTwoAgents测试test集合level2难度**的任务为例

```shell
autogenbench run Tasks/ctfaia_test_level_2__BasicTwoAgents.jsonl
```

6. 本地评估任务的执行情况，并将结果输出到目标任务目录下的result.json文件中，result.json可以被提交到 https://huggingface.co/spaces/autogenCTF/agent_ctf_leaderboard 参与排行榜


```shell
autogenbench tabulate Results/ctfaia_test_level_2__BasicTwoAgents -o
```









