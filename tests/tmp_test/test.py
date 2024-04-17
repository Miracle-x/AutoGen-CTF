from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="gaia-benchmark/GAIA",
    repo_type="dataset",
    local_dir='./dataset',
    local_dir_use_symlinks=True,
)
