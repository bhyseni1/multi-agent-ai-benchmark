# Multi-Agent AI Benchmark — Cross-Provider Experimental Framework

Research code for **OpenAI, Anthropic Claude, and Google Gemini** using official Python SDKs. It uses **live API calls only**. No simulated scores or fabricated results.

## Installation

```bash
python -m venv .venv
# Activate .venv using your operating system's command
pip install -r requirements.txt
python -m pytest -q
```

Create `.env` from `.env.example` and add credentials. Load them into your shell, or use `python-dotenv` (the runner itself reads environment variables and does not automatically load `.env`). Never commit keys.

## Download the public benchmark

```bash
python -m benchmark.prepare --limit 20 --seed 42 --out data/gsm8k_test.csv
```

Dataset: [GSM8K](https://huggingface.co/datasets/openai/gsm8k), official `test` split. This requires internet access. Save the resolved dataset revision before publishing. A CSV SHA256 and manifest are produced.

## Run actual provider experiments

Set keys in the terminal environment (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) and choose **exact model IDs enabled in your own accounts**:

```bash
python -m benchmark.experiment --provider openai --model YOUR_OPENAI_MODEL_ID --dataset data/gsm8k_test.csv --repeats 1
python -m benchmark.experiment --provider anthropic --model YOUR_CLAUDE_MODEL_ID --dataset data/gsm8k_test.csv --repeats 1
python -m benchmark.experiment --provider gemini --model YOUR_GEMINI_MODEL_ID --dataset data/gsm8k_test.csv --repeats 1
```

Each run produces `results/<run_id>.csv`, `<run_id>.traces.jsonl`, and `<run_id>.metadata.json`. Failed API calls remain visible in CSV with error messages. **20 tasks × 4 architectures = 80 architecture evaluations per provider**, involving more than 80 paid API calls. Review cost limits before starting.

## Important

- The old `benchmark.run` is retained for backward compatibility but is **OpenAI-only and uses Chat Completions**. Use `benchmark.experiment` for the cross-provider study.
- Provider token counts are not guaranteed to be equivalent, and latency includes network overhead.
- The included GSM8K pilot does **not** establish a Q1/Q2-level empirical contribution by itself.
- See `PROTOCOL.md` for planned confirmatory design, limitations, and preregistration requirements.
- Official SDK docs: https://developers.openai.com/api/reference/python ; https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python ; https://googleapis.github.io/python-genai/

## Open-data benchmark extension

Prepare two real benchmark test splits, provenance-pinned to Hugging Face repository commits:

```bash
python -m benchmark.prepare --dataset gsm8k --limit 20 --seed 42
python -m benchmark.prepare --dataset arc-challenge --limit 20 --seed 42
```

Use `--dataset data/arc-challenge_test.csv` when running `benchmark.experiment` for ARC.
Read `OPEN_DATA.md` for licensing, provenance and assessment rules. **No live LLM experiment results are included.**

## Independent audit in GitHub Actions

The `Verify benchmark source code` workflow runs unit tests without calling any model APIs. The manually triggered `Verify public benchmark acquisition` workflow downloads actual GSM8K and ARC-Challenge records from Hugging Face, pins source repository revisions, validates counts and hashes, and uploads a short-lived data/provenance artifact. **Neither workflow makes paid model calls.** A successful workflow run is evidence of source retrieval and technical checks, *not* evidence of improved LLM performance.

To run locally:

```bash
python -m benchmark.prepare --dataset gsm8k --limit 20 --seed 42
python -m benchmark.prepare --dataset arc-challenge --limit 20 --seed 42
python -m benchmark.verify_data data/gsm8k_test.csv data/arc-challenge_test.csv
```

For ethical and cost reasons, live OpenAI/Anthropic/Gemini calls are intentionally NOT automatically started in GitHub Actions. Execute `benchmark.experiment` manually with your account-approved model IDs and provider credentials, after reviewing API pricing and study settings. Do not commit API keys or confidential traces.

**Scientific limitation:** GSM8K and ARC are fixed QA benchmarks, not direct measures of real-world multi-agent software-engineering capability. Statistical comparison must separate datasets and models. Matching maximum response-token caps is not equivalent to matching actual token spend across providers.

## Run a verified, real-data experiment on GitHub Actions

See [START_HERE.md](START_HERE.md). The manually dispatched `live-pilot.yml` requires repository API secrets and downloads genuine public task records before live model calls. The artifact includes raw traces, a task manifest and experiment metadata. **No API experiment results are claimed before that workflow has successfully run.**
