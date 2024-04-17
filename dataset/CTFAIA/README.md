---
language:
- en
pretty_name: CTF(Capture The Flag) AI Assistants Benchmark
---

## 编写数据

使用create_test_jsonl.py编写test数据集，编写完成后执行

使用create_val_jsonl.py编写val数据集，编写完成后执行

## 上传数据集至huggingface

登录，你需要是autogenCTF组织成员，并通过官网获取到您的token

```shell
huggingface-cli login
```

上传数据集（仅2024目录）

```shell
huggingface-cli upload autogenCTF/CTFAIA ./2024 ./2024 --repo-type=dataset
```

测试数据集

执行test.py文件，检查是否下载成功


