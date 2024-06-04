import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
rcParams['axes.unicode_minus'] = False    # 解决保存图像时负号 '-' 显示为方块的问题

# 数据
categories = ['1', '2', '3']
overall_data = {
    '无计划模块': [11, 3, 0],
    '无侦察模块': [13, 6, 1],
    '无分析模块': [15, 9, 2],
    '无动作模块': [5, 0, 0]
}

subtask_data = {
    '无计划模块': [92, 35, 0],
    '无侦察模块': [124, 68, 7],
    '无分析模块': [138, 71, 12],
    '无分析模块': [150, 95, 31]
}
# overall_data = {
#     'A': [8, 2, 0],
#     'AP': [11, 5, 0],
#     'APS': [12, 5, 0],
#     'APSR': [15, 9, 2]
# }

# subtask_data = {
#     'A': [92, 35, 0],
#     'AP': [124, 68, 7],
#     'APS': [138, 71, 12],
#     'APSR': [150, 95, 31]
# }

# 设置柱状图的宽度和位置
bar_width = 0.15
index = np.arange(len(categories))

# 绘制总体完成任务数图
plt.figure(figsize=(10, 6))
for i, (label, data) in enumerate(overall_data.items()):
    bars = plt.bar(index + i * bar_width, data, bar_width, label=label)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center', va='bottom')

plt.xlabel('级别')
plt.ylabel('完成任务数')
plt.title('(a) 总完成任务数.')
plt.xticks(index + bar_width * 1.5, categories)
plt.legend()
plt.tight_layout()
plt.show()

# 绘制总得分图
plt.figure(figsize=(10, 6))
for i, (label, data) in enumerate(subtask_data.items()):
    bars = plt.bar(index + i * bar_width, data, bar_width, label=label)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center', va='bottom')

plt.xlabel('级别')
plt.ylabel('总得分')
plt.title('(b) 总得分.')
plt.xticks(index + bar_width * 1.5, categories)
plt.legend()
plt.tight_layout()
plt.show()

