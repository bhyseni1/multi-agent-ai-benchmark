# Open data acquisition & provenance

Two **real public datasets**, accessed from Hugging Face when running `benchmark.prepare` online:

1. GSM8K — `openai/gsm8k`, `main`, `test`. Mathematics word problems, ground-truth answers embedded after `####`. https://huggingface.co/datasets/openai/gsm8k
2. AI2 ARC-Challenge — `allenai/ai2_arc`, `ARC-Challenge`, `test`. Science multiple-choice questions with labels and `answerKey`. https://huggingface.co/datasets/allenai/ai2_arc

Datasets have their own licenses and terms. Check the repository dataset cards before re-distributing individual tasks. A runtime download resolves an immutable Hugging Face repository commit SHA and records a manifest containing revision, indices, sample seed, source URL and CSV SHA-256. Data are not included in source releases to avoid ambiguity about licensing.

## Commands (require internet access)

```bash
python -m benchmark.prepare --dataset gsm8k --limit 20 --seed 42
python -m benchmark.prepare --dataset arc-challenge --limit 20 --seed 42
```

Then call `python -m benchmark.experiment` with `--dataset data/gsm8k_test.csv` or `--dataset data/arc-challenge_test.csv`, a provider and a valid model ID. Results must never be represented as collected until the API calls complete.

**Interpretation:** GSM8K numeric exact match and ARC answer-label accuracy are separate domain-specific outcomes. Do not average them without a preregistered weighting/aggregation definition. Different agent structures make different numbers of paid API requests; compare also against token-/request-matched baselines in confirmatory experiments. Small pilots are NOT evidence of general superiority.
