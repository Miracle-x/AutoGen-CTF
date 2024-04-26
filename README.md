阿里巴巴国际站与西北工业大学联合开发项目</br>
网络空间安全学院-NLP&大模型安全课题组-高德宏&杨黎斌&刘鹏望&胥基&赖起敬&张一涵&周梓伦

[**[LeaderBoard]**](https://huggingface.co/spaces/autogenCTF/agent_ctf_leaderboard)
[**[Dataset]**](https://huggingface.co/datasets/autogenCTF/CTFAIA)
[**[GitHub]**](https://github.com/Miracle-x/AutoGen-CTF)
[**[CTF platform]**](http://47.251.44.45:8000)
[**[Contribute to CTF platform]**](https://github.com/TedLau/Docker-AutoCTF)


## 项目介绍
本项目旨在探索Agent在网络安全领域的实操能力，以CTF题目的解决程度作为检验标准。</br>
包含一个CTF靶场[**[CTF platform]**](http://47.251.44.45:8000)，您可以点击[**[Contribute to CTF platform]**](https://github.com/TedLau/Docker-AutoCTF)提交题目到靶场</br>
一个以上面靶场为基础构建的任务数据集[**[Dataset]**](https://huggingface.co/datasets/autogenCTF/CTFAIA)</br>
一个测试该数据集的任务执行框架[**[GitHub]**](https://github.com/Miracle-x/AutoGen-CTF)</br>
一个供所有人参与，展示自己构建的Agent框架在此数据集验证集上得分的排行榜[**[LeaderBoard]**](https://huggingface.co/spaces/autogenCTF/agent_ctf_leaderboard)</br>

**你可以根据下面的教程进行项目的初体验**


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
# 设置环境变量
# 1 LLM相关环境变量
export OPENAI_API_KEY=<openai_api_key>
export BASE_URL=<base_url>
# 2 autogen所需环境变量，OAI_CONFIG_LIST为根目录下的一个文件，替换其内容中的"<...>"，替换后执行以下代码
export OAI_CONFIG_LIST=$(cat ./OAI_CONFIG_LIST)
# 3 WebSurferAgent所需环境变量（可不设置，要体验此Agent相关功能时会报错）
export BING_API_KEY=<bing_api_key>
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

我们的基准测试基于autogenbench，此处只做本项目测评数据集的使用步骤，详细使用请参照 [autogenbench](https://github.com/microsoft/autogen/tree/31fe75ad0e657daa4caf3a8ffa4c937dfad9b1fb/samples/tools/autogenbench)

1. 安装相关库, 下面两条命令任选一个执行

   a. 安装官方最新版本，此版本构建的docker预装库较少，运行任务会根据agent框架的requirements.txt再去下载相关依赖
   ```shell
   pip install autogenbench==0.0.3
   ```
   b. 安装0.0.2a3版本，此版本构建的docker比较大，已安装好相关依赖
   ```shell
   pip install autogenbench==0.0.2a3
   ```

2. **如果是Windows系统，请确保docker已安装**（linux系统可跳过这一步），安装参考 https://www.docker.com/products/docker-desktop/ 

3. 进入要测试的数据集文件夹

```shell
cd tests/benchmark_test/CTFAIA
```

4. 运行初始化脚本 init_tasks.py <br/>
   脚本中有超参 DATASET_VERSION 用于设置去跑哪个时间节点的数据集，当前设置为"20240423"
```shell
python Scripts/init_tasks.py
```

5. 运行一个任务，此处以**使用BasicTwoAgents测试20240423数据集test集合level1难度**的任务为例

   a. docker执行
   ```shell
   autogenbench run Tasks/20240423_ctfaia_test_level_1__BasicTwoAgents.jsonl
   ```
   b. 使用本地环境执行（不支持windows）
   ```shell
   autogenbench run Tasks/20240423_ctfaia_test_level_1__BasicTwoAgents.jsonl --native
   ```

6. 本地输出任务的执行情况，并将结果输出到目标任务目录下的result.jsonl文件中，
result.json可以被提交到 [**[LeaderBoard]**](https://huggingface.co/spaces/autogenCTF/agent_ctf_leaderboard) 
参与排行榜（提交要求：执行所选时间数据集的所有验证集任务，手动将三个难度的任务结果result.jsonl放在同一个jsonl文件中提交）

```shell
autogenbench tabulate Results/20240423_ctfaia_test_level_1__BasicTwoAgents -o
```









