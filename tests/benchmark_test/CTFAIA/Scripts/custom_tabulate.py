import argparse
import json
import os
import re
import sys
from copy import deepcopy

import tabulate as tb
from autogenbench.tabulate_cmd import default_tabulate, default_scorer, EXCLUDE_DIR_NAMES


def normalize_answer(a):
    # Lower case
    # Trim (left and right)
    # Replace multiple spaces with one space
    # Remove trailing punctuation
    # return re.sub(r"[\.\!\?]+$", "", re.sub(r"\s+", " ", a.strip().lower()))
    return a


def scorer(instance_dir):
    # Read the expected answer
    expected_answer_file = os.path.join(instance_dir, "expected_answer.txt")
    if not os.path.isfile(expected_answer_file):
        return None
    expected_answer = None
    with open(expected_answer_file, "rt") as fh:
        expected_answer = fh.read().strip()

    # Read the console
    console_log_file = os.path.join(instance_dir, "console_log.txt")
    if not os.path.isfile(console_log_file):
        return None

    console_log = ""
    print(console_log_file)
    with open(console_log_file, "rt", encoding="utf-8") as fh:
        console_log = fh.read()

        final_answer = ""
        m = re.search(r"FINAL ANSWER:(.*?)\n", console_log, re.DOTALL)
        if m:
            final_answer = m.group(1).strip()

        # # Return true if they are equal after normalization
        # return normalize_answer(expected_answer) == normalize_answer(final_answer)
        # 新的打分机制
        score = 0
        if normalize_answer(expected_answer) == normalize_answer(final_answer):
            score = 10
            return score
        else:
            # 读取chat_score
            chat_score_file = os.path.join(instance_dir, "chat_score.txt")
            if not os.path.isfile(chat_score_file):
                return None
            chat_score = None
            with open(chat_score_file, "rt") as fh:
                chat_score = eval(fh.read().strip())
            for i, score_item in enumerate(chat_score):
                m = re.search(rf"Answer{i}:(.*?)\n", console_log, re.DOTALL)
                if m:
                    answer = m.group(1).strip()
                    if answer in score_item['answer'] and score_item['score'] > score:
                        score = score_item['score']
            return score


def custom_tabulate(args, scorer=default_scorer, exclude_dir_names=EXCLUDE_DIR_NAMES):
    invocation_cmd = args[0]
    args = args[1:]

    warning = f"CAUTION: '{invocation_cmd}' is in early preview and is not thoroughly tested.\nPlease do not cite values from these calculations in academic work without first inspecting and verifying the results in the run logs yourself."

    # Prepare the argument parser
    parser = argparse.ArgumentParser(
        prog=invocation_cmd,
        description=f"{invocation_cmd} will tabulate the results of a previous run.",
    )

    parser.add_argument(
        "runlogs",
        help="The path where the run's logs are stored.",
    )
    parser.add_argument(
        "-c",
        "--csv",
        action="store_true",
        help="Output the results in CSV format.",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="Output the results in jsonl format. Please specify a path for the jsonl file."
    )

    parsed_args = parser.parse_args(args)

    all_results = list()
    max_instances = 0

    for task_id in sorted(
            os.listdir(parsed_args.runlogs),
            key=lambda s: os.path.getmtime(os.path.join(parsed_args.runlogs, s)),
    ):
        if task_id in exclude_dir_names:
            continue

        task_path = os.path.join(parsed_args.runlogs, task_id)

        if not os.path.isdir(task_path):
            continue

        # Collect the results vector
        results = [task_id]

        instance = 0
        instance_dir = os.path.join(task_path, str(instance))
        while os.path.isdir(instance_dir):
            results.append(scorer(instance_dir))
            instance += 1
            instance_dir = os.path.join(task_path, str(instance))

        max_instances = max(max_instances, instance)

        # Buffer the results
        all_results.append(results)

    if parsed_args.csv:
        # Create a header
        header = ["Task Id"]
        for i in range(0, max_instances):
            header.append("Trial " + str(i) + " Score")

        print(",".join(header))
        for row in all_results:
            str_row = [f"{v}" if v is not None else "" for v in row]
            while len(str_row) < max_instances + 1:
                str_row.append("")
            print(",".join(str_row))

        # Print out alpha-version warning
        sys.stderr.write("\n" + warning + "\n\n")
    else:
        # Create a header
        header = ["\nTask Id"]
        for i in range(0, max_instances):
            header.append("Trial " + str(i) + "\nScore")

        # Create the footer
        def _count_equals(value, trial):
            count = 0
            for row in all_results:
                # Count missing
                if value is None:
                    if trial + 1 < len(row):
                        if row[trial + 1] is None:
                            count += 1
                    else:
                        count += 1
                # Count match
                elif trial + 1 < len(row) and row[trial + 1] == value:
                    count += 1
            return count

        footer = []
        footer_row = ["Successes"]
        for i in range(0, max_instances):
            footer_row.append(_count_equals(True, i))
        footer.append(footer_row)

        footer_row = ["Failures"]
        for i in range(0, max_instances):
            footer_row.append(_count_equals(False, i))
        footer.append(footer_row)

        footer_row = ["Missing"]
        for i in range(0, max_instances):
            footer_row.append(_count_equals(None, i))
        footer.append(footer_row)

        footer_row = ["Total"]
        for i in range(0, max_instances):
            footer_row.append(footer[0][i + 1] + footer[1][i + 1] + footer[2][i + 1])
        footer.append(footer_row)

        table = deepcopy(all_results)
        for row in table:
            for trial in range(0, max_instances):
                if isinstance(row[trial + 1], tuple):
                    row[trial + 1] = row[trial + 1][0]

        table.append(tb.SEPARATING_LINE)
        # table.extend(footer)

        print(tb.tabulate(table, headers=header))

        # Print out alpha-version warning
        sys.stderr.write("\n" + warning + "\n\n")

    # 根据参数输出jsonl格式，目前只生成repeat0的结果
    if parsed_args.output:
        results_jsonl = []
        for task_id in sorted(
                os.listdir(parsed_args.runlogs),
                key=lambda s: os.path.getmtime(os.path.join(parsed_args.runlogs, s)),
        ):
            if task_id in exclude_dir_names:
                continue

            result_json = {"task_name": task_id}
            task_path = os.path.join(parsed_args.runlogs, task_id)

            if not os.path.isdir(task_path):
                continue

            instance = 0
            instance_dir = os.path.join(task_path, str(instance))

            console_log_file = os.path.join(instance_dir, "console_log.txt")
            if not os.path.isfile(console_log_file):
                continue

            console_log = ""
            print(console_log_file)
            with open(console_log_file, "rt", encoding="utf-8") as fh:
                console_log = fh.read()

                m = re.search(r"FINAL ANSWER:(.*?)\n", console_log, re.DOTALL)
                if m:
                    result_json["final_answer"] = m.group(1).strip()
                else:
                    result_json["final_answer"] = ""

                chat_score_file = os.path.join(instance_dir, "chat_score.txt")
                chat_score = None
                with open(chat_score_file, "rt") as fh:
                    chat_score = eval(fh.read().strip())
                result_json["score_answer"] = []
                for i, score_item in enumerate(chat_score):
                    m = re.search(rf"Answer{i}:(.*?)\n", console_log, re.DOTALL)
                    if m:
                        result_json["score_answer"].append(m.group(1).strip())
                    else:
                        result_json["score_answer"].append("")
            results_jsonl.append(result_json)
        with open(os.path.join(parsed_args.runlogs, 'result.jsonl'), 'w') as file:
            for item in results_jsonl:
                file.write(json.dumps(item) + '\n')
        print(os.path.join(parsed_args.runlogs, 'result.jsonl'))


def main(args):
    custom_tabulate(args, scorer=scorer)


if __name__ == "__main__" and __package__ is None:
    main(sys.argv)
