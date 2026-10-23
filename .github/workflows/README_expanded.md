# Expanded paired open-weight experiment

This is a runnable GitHub Actions workflow, **not a completed experiment**.

Upload `expanded-open-weight.yml` into `.github/workflows/` in `bhyseni1/multi-agent-ai-benchmark`.

Launch **Expanded open-weight paired benchmark (two models)** with 100 tasks and 1 repeat. The matrix runs `google/flan-t5-small` and `google/flan-t5-base` separately on the same ARC-Challenge test indices using seed 42. It downloads the actual model weights and dataset from Hugging Face, resolves immutable revision SHAs, and executes real local CPU inference. It makes no paid OpenAI API calls.

Each job publishes an artifact with raw question IDs, ground truth, raw output strings, parsed answers, per-task tokenizer counts, inference timings, `summary.json`, `summary.csv`, `metadata.json`, raw SHA-256, package versions, and the executed script. McNemar exact and paired bootstrap confidence interval are computed per model; these are exploratory, **not a Q1/Q2 contribution claim**.

## Scientific limitations

- Only two prompt-based inference strategies are compared, not two different independent agent models. The Two-Role result reuses the Single-Agent draft, then does a second model call.
- The input lengths differ by architecture, and the same FLAN weights are used for both roles.
- Latency on a shared GitHub runner is hardware-dependent. Report observed latency, not provider pricing.
- The random 100-question sample is a subset of ARC-Challenge test split. 100 tasks do not automatically establish generalizability or novelty.
- Comparing across the two model sizes tests robustness, not multiple independent model families.
- Research publication needs an additional dataset, budget-matched two-call baseline, repeated seeds, effect-size uncertainty, and review of any model contamination limitations.
- Never mix unit-test fixture data with empirical inference observations.
- Unparsable responses are scored incorrect, with raw text preserved; do not omit failures.

## Evidence and interpretation

**A green workflow alone does not prove model superiority.** Download each model's artifact and validate all JSONL rows before scientific interpretation. Any job failure yields `FAILURE.txt` and should not be counted as a completed comparison.
