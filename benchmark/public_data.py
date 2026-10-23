"""Public benchmark acquisition; no synthetic replacements or fabricated observations."""
import csv, hashlib, json, random
from pathlib import Path
from datetime import datetime, timezone

SOURCES = {
    "gsm8k": ("openai/gsm8k", "main", "test"),
    "arc-challenge": ("allenai/ai2_arc", "ARC-Challenge", "test"),
}

def normalize_record(dataset, example):
    if dataset == "gsm8k":
        answer = example["answer"].rsplit("####", 1)
        if len(answer) != 2: raise ValueError("GSM8K answer missing #### delimiter")
        return {"task_id":"gsm8k:"+hashlib.sha256(example["question"].encode()).hexdigest()[:16],
                "dataset":dataset,"answer_type":"number","prompt":example["question"],
                "expected":answer[-1].strip().replace(",", "")}
    if dataset == "arc-challenge":
        choices = example["choices"]
        labels = [str(x).strip().upper() for x in choices["label"]]
        answer = str(example["answerKey"]).strip().upper()
        if answer not in labels: raise ValueError("ARC answerKey not in provided choice labels")
        options = "\n".join(f"{lab}. {txt}" for lab, txt in zip(labels, choices["text"]))
        return {"task_id":"arc:"+str(example["id"]),"dataset":dataset,
                "answer_type":"choice","prompt":example["question"]+"\nOptions:\n"+options,
                "expected":answer}
    raise ValueError("Unrecognized dataset: "+dataset)

def prepare_public(dataset="gsm8k",out=None,limit=100,seed=42,revision=None):
    if dataset not in SOURCES: raise ValueError(f"Unknown dataset: {dataset}")
    if limit < 1: raise ValueError("limit must be positive")
    from datasets import load_dataset
    from huggingface_hub import HfApi
    repo,config,split=SOURCES[dataset]
    # Freeze current revision via the HF repository's immutable full commit SHA.
    resolved=HfApi().dataset_info(repo,revision=revision or "main").sha
    if not resolved: raise RuntimeError("Could not resolve dataset revision")
    ds=load_dataset(repo,name=config,split=split,revision=resolved)
    indices=random.Random(seed).sample(range(len(ds)),min(limit,len(ds)))
    rows=[normalize_record(dataset,ds[i]) for i in indices]
    dest=Path(out or f"data/{dataset}_test.csv")
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["task_id","dataset","answer_type","prompt","expected"])
        writer.writeheader();writer.writerows(rows)
    manifest={"source_platform":"Hugging Face Datasets","source_url":f"https://huggingface.co/datasets/{repo}",
              "repository":repo,"config":config,"split":split,"revision_sha":resolved,
              "sampling_seed":seed,"sampling_method":"python_random_sample_without_replacement",
              "sample_indices":indices,"rows":len(rows),"csv_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
              "retrieved_utc":datetime.now(timezone.utc).isoformat(),
              "note":"Dataset records downloaded at execution time, not simulated."}
    dest.with_suffix(".manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return dest

def prepare_gsm8k(out="data/gsm8k_test.csv",limit=100,seed=42):
    return prepare_public("gsm8k",out,limit,seed)
