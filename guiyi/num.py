import json

# 定义八种攻击类型
attack_types = [
    "SQL Injection",
    "File Upload",
    "XSS",
    "SSTI",
    "Deserialization",
    "PHP Feature",
    "Code Audit",
    "RCE&Pseudo Protocol"
]

# 初始化计数器
attack_counts = {attack: 0 for attack in attack_types}

# 读取JSONL文件并统计攻击类型数量
file_path = "C:/Users/blacksun/Documents/网安/pythonproject/AutoGen-CTF/2024/validation/20240531metadata.jsonl"
with open(file_path, 'r', encoding='utf-8') as file:
    for line in file:
        data = json.loads(line.strip())
        key_labels = data.get("Key labels", [])
        
        # 打印读取的字段以供调试
        print(f"Key labels: {key_labels}")

        for attack in attack_types:
            if attack in key_labels:
                attack_counts[attack] += 1

# 打印结果
for attack, count in attack_counts.items():
    print(f"{attack}: {count}")

