from datasets import load_dataset

dataset = load_dataset("autogenCTF/CTFAIA", cache_dir='.', download_mode="force_redownload")