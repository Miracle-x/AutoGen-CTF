from datasets import load_dataset
import json

# dataset = load_dataset("autogenCTF/CTFAIA", cache_dir='.', download_mode="force_redownload")

def load_jsonl(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            json_obj = json.loads(line)
            data.append(json_obj)
    return data

def print_json_data(data):
    for entry in data:
        json_str = json.dumps(entry, indent=4)
        print(json_str+',')

json_list = load_jsonl('2024_test_metadata.jsonl')
print_json_data(json_list)