import os
from agents.webarena_browser_agent import WebarenaBrowserAgent

if __name__ == "__main__":
    print(os.environ.get("OPENAI_API_KEY"))
    print(os.environ.get("BASE_URL"))
    print(os.environ)

