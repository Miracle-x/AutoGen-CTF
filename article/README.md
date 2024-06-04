# 数据集编写流程

## 编写初始数据
在data_create文件夹中， 仿照 [SUCTF 2019]EasySQL.py 内容编写prompt

## 获得参考系context
在get_context文件夹中，仿照 test_user_with_agent_doing.py 进行对话，对话使用刚刚编写的prompt，保存对话记录为context

## 编写问题并验证问题
在eval文件夹中，仿照 answer_q.py 编写问题并利用脚本验证在拥有context下，可被LLM答出，证明问题有效

## 生成抽象能力比率
在debateGroup文件夹中，仿照 debateGroup.py 文件，让各LLM讨论出问题所表现的3个抽象能力的重要占比，确定最终dataset是什么样，放在[SUCTF 2019]EasySQL.py文件中
