#
# Run this file to download the human_eval dataset, and create a corresponding testbed scenario:
# (default: ../scenarios/human_eval_two_agents_gpt4.jsonl and ./scenarios/human_eval_two_agents_gpt35.jsonl)
#

import json
import os
import re
import sys

from huggingface_hub import snapshot_download

# 路径设置
SCRIPT_PATH = os.path.realpath(__file__)
SCRIPT_NAME = os.path.basename(SCRIPT_PATH)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)

SCENARIO_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, os.path.pardir))
TEMPLATES_DIR = os.path.join(SCENARIO_DIR, "Templates")
TASKS_DIR = os.path.join(SCENARIO_DIR, "Tasks")
DOWNLOADS_DIR = os.path.join(SCENARIO_DIR, "Downloads")
REPO_DIR = os.path.join(DOWNLOADS_DIR, "CTFAIA")

# 是否使用硬编码（硬编码是我们用来提示LLM如何解决这道题的prompt，如果想严格评估LLM Agent的能力，请设置此变量为False）
USE_HARD_PROMPT = False

# 初始化该目录的数据集
DATASET_VERSION = "20240602"


def download_ctfaia():
    """Download the CTFAIA benchmark from Hugging Face."""

    if not os.path.isdir(DOWNLOADS_DIR):
        os.mkdir(DOWNLOADS_DIR)

    """Download the CTFAIA dataset from Hugging Face Hub"""
    snapshot_download(
        repo_id="autogenCTF/CTFAIA",
        repo_type="dataset",
        local_dir=REPO_DIR,
        local_dir_use_symlinks=True,
        token=os.getenv('HUGGINGFACE_API_KEY')
    )


def create_jsonl(name, tasks, files_dir, template):
    """Creates a JSONL scenario file with a given name, and template path."""

    if not os.path.isdir(TASKS_DIR):
        os.mkdir(TASKS_DIR)

    with open(os.path.join(TASKS_DIR, name + ".jsonl"), "wt") as fh:
        for task in tasks:
            print(f"Converting: [{name}] {task['task_name']}")

            # Figure out what files we need to copy
            template_cp_list = [template]
            if len(task["Annex"].strip()) > 0:
                template_cp_list.append(
                    [
                        os.path.join(files_dir, task["Annex"].strip()),
                        os.path.join("coding", task["Annex"].strip()),
                    ]
                )
            prompt = task["Question"].format(url=task["url"])
            if USE_HARD_PROMPT:
                prompt += '\n\n'
                prompt += 'You can refer to the following steps to complete the task:\n'
                prompt += task['prompt']
            record = {
                "id": task["task_name"],
                "template": template_cp_list,
                "substitutions": {
                    "scenario.py": {
                        "__ANNEX__": task["Annex"]
                    },
                    "chat_score.txt": {"__SCORE__": str(task["score"])},
                    "expected_answer.txt": {"__EXPECTED_ANSWER__": task["Final answer"]},
                    "prompt.txt": {"__PROMPT__": prompt},
                },
            }

            fh.write(json.dumps(record).strip() + "\n")


###############################################################################
def main():
    download_ctfaia()
    ctfaia_validation_files = os.path.join(REPO_DIR,DATASET_VERSION,"validation")
    ctfaia_test_files = os.path.join(REPO_DIR,DATASET_VERSION,"test")

    if not os.path.isdir(ctfaia_validation_files) or not os.path.isdir(ctfaia_test_files):
        sys.exit(f"Error: '{REPO_DIR}' does not appear to be a copy of the CTFAIA repository.")

    # Load the CTFAIA data
    ctfaia_validation_tasks = [[], [], []]
    all_tasks = []
    with open(os.path.join(ctfaia_validation_files, "metadata.jsonl")) as fh:
        for line in fh:
            data = json.loads(line)
            ctfaia_validation_tasks[data["Level"] - 1].append(data)
            all_tasks.append(data)

    ctfaia_test_tasks = [[], [], []]
    with open(os.path.join(ctfaia_test_files, "metadata.jsonl"), encoding='utf-8') as fh:
        for line in fh:
            data = json.loads(line)

            # A welcome message -- not a real task
            if data["task_name"] == "this is the format":
                continue

            ctfaia_test_tasks[data["Level"] - 1].append(data)
            all_tasks.append(data)

    # list all directories in the Templates directory
    # and populate a dictionary with the name and path
    templates = {}
    for entry in os.scandir(TEMPLATES_DIR):
        if entry.is_dir():
            templates[re.sub(r"\s", "", entry.name)] = entry.path

    # Add coding directories if needed (these are usually empty and left out of the repo)
    for template in templates.values():
        code_dir_path = os.path.join(template, "coding")
        if not os.path.isdir(code_dir_path):
            os.mkdir(code_dir_path)

    # Create the various combinations of [models] x [templates]
    for t in templates.items():
        create_jsonl(
            f"{t[0]}__ctfaia__all__{DATASET_VERSION}",
            all_tasks,
            ctfaia_validation_files,
            t[1],
        )
        # create_jsonl(
        #     DATASET_VERSION + f"_ctfaia_validation_level_1__{t[0]}",
        #     ctfaia_validation_tasks[0],
        #     ctfaia_validation_files,
        #     t[1],
        # )
        # create_jsonl(
        #     DATASET_VERSION+f"_ctfaia_validation_level_2__{t[0]}",
        #     ctfaia_validation_tasks[1],
        #     ctfaia_validation_files,
        #     t[1],
        # )
        # create_jsonl(
        #     DATASET_VERSION+f"_ctfaia_validation_level_3__{t[0]}",
        #     ctfaia_validation_tasks[2],
        #     ctfaia_validation_files,
        #     t[1],
        # )
        # create_jsonl(
        #     DATASET_VERSION+f"_ctfaia_test_level_1__{t[0]}",
        #     ctfaia_test_tasks[0],
        #     ctfaia_test_files,
        #     t[1],
        # )
        # create_jsonl(
        #     DATASET_VERSION+f"_ctfaia_test_level_2__{t[0]}",
        #     ctfaia_test_tasks[1],
        #     ctfaia_test_files,
        #     t[1],
        # )
        # create_jsonl(
        #     DATASET_VERSION+f"_ctfaia_test_level_3__{t[0]}",
        #     ctfaia_test_tasks[2],
        #     ctfaia_test_files,
        #     t[1],
        # )


if __name__ == "__main__":
    main()
