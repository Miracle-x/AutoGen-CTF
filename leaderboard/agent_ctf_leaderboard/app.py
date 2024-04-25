import os
import json
import datetime
from email.utils import parseaddr

import gradio as gr
import pandas as pd
import numpy as np

from datasets import load_dataset
from apscheduler.schedulers.background import BackgroundScheduler
from huggingface_hub import HfApi, snapshot_download

# InfoStrings
from scorer import question_scorer
from content import format_error, format_warning, format_log, TITLE, INTRODUCTION_TEXT, CITATION_BUTTON_LABEL, \
    CITATION_BUTTON_TEXT, model_hyperlink

TOKEN = os.environ.get("TOKEN", None)

OWNER = "autogenCTF"
DATA_DATASET = f"{OWNER}/CTFAIA"
INTERNAL_DATA_DATASET = f"{OWNER}/CTFAIA_internal"
SUBMISSION_DATASET = f"{OWNER}/CTFAIA_submissions_internal"
CONTACT_DATASET = f"{OWNER}/contact_info"
RESULTS_DATASET = f"{OWNER}/CTFAIA_results_public"
LEADERBOARD_PATH = f"{OWNER}/agent_ctf_leaderboard"
api = HfApi()

YEAR_VERSION = "2024"

os.makedirs("scored", exist_ok=True)

"""Download the CTFAIA dataset from Hugging Face Hub"""
snapshot_download(
    repo_id="autogenCTF/CTFAIA",
    repo_type="dataset",
    local_dir='./CTFAIA',
    local_dir_use_symlinks=True,
    token=TOKEN
)


def get_all_folders(directory):
    folders = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            folders.append(str(item))
    return folders


all_version = get_all_folders('./CTFAIA')

eval_results = {}
for dataset_version in all_version:
    eval_results[dataset_version] = load_dataset(
        RESULTS_DATASET, dataset_version,
        token=TOKEN,
        download_mode="force_redownload",
        ignore_verifications=True
    )

contact_infos = load_dataset(CONTACT_DATASET, token=TOKEN, download_mode="force_redownload",
                             ignore_verifications=True)


def get_dataframe_from_results(eval_results, split):
    local_df = eval_results[split]
    local_df = local_df.map(lambda row: {"model": model_hyperlink(row["url"], row["model"])})
    local_df = local_df.remove_columns(["system_prompt", "url"])
    local_df = local_df.rename_column("model", "Model name")
    local_df = local_df.rename_column("model_family", "Model family")
    local_df = local_df.rename_column("score", "Average score (%)")
    for i in [1, 2, 3]:
        local_df = local_df.rename_column(f"score_level{i}", f"Level {i} score (%)")
    df = pd.DataFrame(local_df)
    df = df.sort_values(by=["Average score (%)"], ascending=False)

    numeric_cols = [c for c in local_df.column_names if "score" in c]
    df[numeric_cols] = df[numeric_cols].multiply(100).round(decimals=2)
    # df = df.style.format("{:.2%}", subset=numeric_cols)

    return df


eval_dataframe = {}
for dataset_version in all_version:
    eval_dataframe[dataset_version] = get_dataframe_from_results(
        eval_results=eval_results[dataset_version],
        split="validation"
    )


def restart_space():
    api.restart_space(repo_id=LEADERBOARD_PATH, token=TOKEN)


TYPES = ["markdown", "number", "number", "number", "number", "str", "str"]


def add_new_eval(
        dataset_version: str,
        model: str,
        model_family: str,
        system_prompt: str,
        url: str,
        path_to_file: str,
        organisation: str,
        mail: str,
):
    val_or_test = 'validation'
    # Very basic email parsing
    _, parsed_mail = parseaddr(mail)
    if not "@" in parsed_mail:
        return format_warning("Please provide a valid email adress.")

    print("Adding new eval")

    # Check if the combination model/org already exists and prints a warning message if yes
    if model.lower() in set([m.lower() for m in eval_results[dataset_version][val_or_test]["model"]]) and organisation.lower() in set(
            [o.lower() for o in eval_results[dataset_version][val_or_test]["organisation"]]):
        return format_warning("This model has been already submitted.")

    if path_to_file is None:
        return format_warning("Please attach a file.")

    # Save submitted file
    api.upload_file(
        repo_id=SUBMISSION_DATASET,
        path_or_fileobj=path_to_file.name,
        path_in_repo=f"{organisation}/{model}/{dataset_version}_{val_or_test}_raw_{datetime.datetime.today()}.jsonl",
        repo_type="dataset",
        token=TOKEN
    )

    # Gold answers
    gold_results = {}
    gold_dataset = load_dataset('./CTFAIA/' + dataset_version)
    gold_results = {split: {row["task_name"]: row for row in gold_dataset[split]} for split in ["test", "validation"]}

    # Compute score
    file_path = path_to_file.name
    scores = {"all": 0, 1: 0, 2: 0, 3: 0}
    num_questions = {"all": 0, 1: 0, 2: 0, 3: 0}
    total_scores = {"all": 0, 1: 0, 2: 0, 3: 0}
    with open(f"scored/{organisation}_{model}.jsonl", "w") as scored_file:
        with open(file_path, 'r') as f:
            for ix, line in enumerate(f):
                try:
                    task = json.loads(line)
                except Exception:
                    return format_error(f"Line {ix} is incorrectly formatted. Please fix it and resubmit your file.")

                print(task)
                if "final_answer" not in task:
                    raise format_error(f"Line {ix} contains no final_answer key. Please fix it and resubmit your file.")
                answer = task["final_answer"]
                task_name = task["task_name"]
                try:
                    level = int(gold_results[val_or_test][task_name]["Level"])
                except KeyError:
                    return format_error(
                        f"{task_name} not found in split {val_or_test}. Are you sure you submitted the correct file?")

                score = question_scorer(task, gold_results[val_or_test][task_name])

                scored_file.write(
                    json.dumps({
                        "id": task_name,
                        "final_answer": answer,
                        "score": score,
                        "level": level
                    }) + "\n"
                )

                scores["all"] += score
                scores[level] += score
                num_questions["all"] += 1
                num_questions[level] += 1
    for task_name, task in gold_results[val_or_test].items():
        level = task['Level']
        total_scores["all"] += 10
        total_scores[level] += 10

    # Save scored file
    api.upload_file(
        repo_id=SUBMISSION_DATASET,
        path_or_fileobj=f"scored/{organisation}_{model}.jsonl",
        path_in_repo=f"{organisation}/{model}/{dataset_version}_{val_or_test}_scored_{datetime.datetime.today()}.jsonl",
        repo_type="dataset",
        token=TOKEN
    )

    # Actual submission
    eval_entry = {
        "model": model,
        "model_family": model_family,
        "system_prompt": system_prompt,
        "url": url,
        "organisation": organisation,
        "score": scores["all"] / total_scores["all"],
        "score_level1": scores[1] / total_scores[1] if total_scores[1] else 0,
        "score_level2": scores[2] / total_scores[2] if total_scores[2] else 0,
        "score_level3": scores[3] / total_scores[3] if total_scores[3] else 0,
    }
    eval_results[dataset_version][val_or_test] = eval_results[dataset_version][val_or_test].add_item(eval_entry)
    print(eval_results)
    eval_results[dataset_version].push_to_hub(RESULTS_DATASET, config_name=dataset_version, token=TOKEN)

    contact_info = {
        "model": model,
        "model_family": model_family,
        "url": url,
        "organisation": organisation,
        "mail": mail,
    }
    contact_infos[val_or_test] = contact_infos[val_or_test].add_item(contact_info)
    contact_infos.push_to_hub(CONTACT_DATASET, config_name=YEAR_VERSION, token=TOKEN)

    return format_log(
        f"Model {model} submitted by {organisation} successfully. \nPlease refresh the leaderboard, and wait a bit to see the score displayed")


def refresh():
    eval_results = {}
    for dataset_version in all_version:
        eval_results[dataset_version] = load_dataset(
            RESULTS_DATASET, dataset_version,
            token=TOKEN,
            download_mode="force_redownload",
            ignore_verifications=True
        )
    leaderboard_tables = []
    for dataset_version in all_version:
        eval_dataframe[dataset_version] = get_dataframe_from_results(
            eval_results=eval_results[dataset_version],
            split="validation"
        )
        with gr.Tab(dataset_version):
            leaderboard_tables.append(
                gr.components.Dataframe(
                    value=eval_dataframe[dataset_version], datatype=TYPES, interactive=False,
                    column_widths=["20%"]
                )
            )
    return leaderboard_tables


def upload_file(files):
    file_paths = [file.name for file in files]
    return file_paths


demo = gr.Blocks()
with demo:
    gr.HTML(TITLE)
    gr.Markdown(INTRODUCTION_TEXT, elem_classes="markdown-text")

    with gr.Row():
        with gr.Accordion("📙 Citation", open=False):
            citation_button = gr.Textbox(
                value=CITATION_BUTTON_TEXT,
                label=CITATION_BUTTON_LABEL,
                elem_id="citation-button",
            )  # .style(show_copy_button=True)

    leaderboard_tables = []
    for dataset_version in all_version:
        with gr.Tab(dataset_version):
            leaderboard_tables.append(
                gr.components.Dataframe(
                    value=eval_dataframe[dataset_version], datatype=TYPES, interactive=False,
                    column_widths=["20%"]
                )
            )

    refresh_button = gr.Button("Refresh")
    refresh_button.click(
        refresh,
        inputs=[],
        outputs=leaderboard_tables,
    )
    with gr.Accordion("Submit a new model for evaluation"):
        with gr.Row():
            with gr.Column():
                level_of_test = gr.Radio(all_version, value=all_version[0], label="dataset_version")
                model_name_textbox = gr.Textbox(label="Model name", value='')
                model_family_textbox = gr.Textbox(label="Model family", value='')
                system_prompt_textbox = gr.Textbox(label="System prompt example", value='')
                url_textbox = gr.Textbox(label="Url to model information", value='')
            with gr.Column():
                organisation = gr.Textbox(label="Organisation", value='')
                mail = gr.Textbox(
                    label="Contact email (will be stored privately, & used if there is an issue with your submission)",
                    value='')
                file_output = gr.File()

        submit_button = gr.Button("Submit Eval")
        submission_result = gr.Markdown()
        submit_button.click(
            add_new_eval,
            [
                level_of_test,
                model_name_textbox,
                model_family_textbox,
                system_prompt_textbox,
                url_textbox,
                file_output,
                organisation,
                mail
            ],
            submission_result,
        )

scheduler = BackgroundScheduler()
scheduler.add_job(restart_space, "interval", seconds=3600)
scheduler.start()
demo.launch(debug=True)
