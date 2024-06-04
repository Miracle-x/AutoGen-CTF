---
language:
- en
pretty_name: CTF(Capture The Flag) AI Assistants Benchmark
---

阿里巴巴国际站与西北工业大学联合开发项目

网络空间安全学院-NLP&大模型安全课题组-高德宏&杨黎斌&刘鹏望&胥基&赖起敬&张一涵&周梓伦&张诗扬&刘苗苗&王义翔

[**[LeaderBoard]**](https://huggingface.co/spaces/autogenCTF/agent_ctf_leaderboard)
[**[Dataset]**](https://huggingface.co/datasets/autogenCTF/CTFAIA)
[**[GitHub]**](https://github.com/Miracle-x/AutoGen-CTF)
[**[CTF platform]**](http://47.251.44.45:8000)
[**[Contribute to CTF platform]**](https://github.com/TedLau/Docker-AutoCTF)

# CTFAIA dataset

CTFAIA is a benchmark which aims to evaluate the performance of next-generation LLMs in the field of cybersecurity, particularly CTF competition issues.

We added gating to prevent bots from scraping the dataset. Please do not reshare the validation or test set in a crawlable format.

## Data and leaderboard
CTFAIA is made of more than 100 non-trivial question with an unambiguous answer, requiring different levels of tooling and autonomy to solve. It is therefore divided in 3 levels, where level 1 may not need to use any tools to solve, level 2 requires 1-2 tools and considerable logic ability to achieve, level 3 not only requires the flexible application of tools, but also requires LLMs to have strong reasoning ability and judgment ability, as well as independent exploration.. Each version of the question is divided into a fully public dev set for validation, and a test set with private answers and metadata.

CTFAIA leaderboard can be found in this space (https://huggingface.co/spaces/autogenCTF/agent_ctf_leaderboard).

CTFAIA data can be found in [this dataset](https://huggingface.co/datasets/autogenCTF/CTFAIA). Questions are contained in `metadata.jsonl`. Some questions come with an additional folder, that can be found in the folder and whose id is given in the field `Annex`.
