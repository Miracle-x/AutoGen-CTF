# 数据集编写流程

## 编写初始数据
在data_create文件夹中， 仿照 [SUCTF 2019]EasySQL.py 内容编写，问题先空着

## 获得参考系context
在get_context文件夹中，仿照 test_user_with_agent_doing.py 进行对话，使用刚刚编写的prompt，保存对话记录为context

## 编写问题并验证问题
在eval文件夹中，仿照 answer_q.py 编写问题并利用脚本验证可被LLM答出

## 生成抽象能力比率
在debateGroup文件夹中，仿照 debateGroup.py 文件，让各LLM讨论出结果，填入问题，并最后放在[SUCTF 2019]EasySQL.py文件中
