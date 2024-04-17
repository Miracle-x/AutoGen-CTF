import os

if __name__ == "__main__":
    print(os.environ.get("TEST"))
    print(os.environ.get("OPENAI_API_KEY"))
    print(os.environ.get("BASE_URL"))
    print(os.environ.get("OAI_CONFIG_LIST"))
    print(os.environ)

