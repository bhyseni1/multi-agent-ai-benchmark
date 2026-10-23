# How to obtain real, auditable experimental measurements

1. Upload the files from this folder (not the ZIP as a single file) to `bhyseni1/multi-agent-ai-benchmark` using GitHub's **Add file > Upload files** or Git CLI. `.github/workflows/live-pilot.yml` must retain its subdirectory path.
2. Inspect `.github/workflows/ci.yml` and `.github/workflows/public-data-check.yml` and ensure Actions is enabled.
3. Under **Settings > Secrets and variables > Actions**, create `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`. Do not paste secrets into a chat, issue, commit, or notebook.
4. Under **Actions > Verify public benchmark acquisition > Run workflow**, download actual benchmark items first. The resulting artifact includes source URLs, 40-character immutable dataset commit SHAs, item IDs, and CSV SHA-256.
5. Under **Actions > Live paid API benchmark pilot > Run workflow**, choose one provider, its exact model ID, a dataset, 5 tasks and 1 repeat. Repeat separately for each provider/model and both datasets. This makes live paid API calls.
6. Download the run artifact (CSV + raw response traces + metadata + manifest + `pip freeze`). Keep all error rows and API request failures. Preserve GitHub workflow run URL, UTC execution time, and commit SHA for the paper.

**Important:** Unit tests use small fixtures only to verify code behavior; fixtures are *never* empirical AI performance data. A green CI badge does not mean real OpenAI/Claude/Gemini calls happened. No score, latency, token count, or cost is claimed until `Live paid API benchmark pilot` actually runs.

**Research safeguards:** freeze the model ID and revision, avoid benchmark contamination claims, predefine successful-score parsing, separately analyze each dataset, quantify uncertainty, and implement token-budget-matched baselines before Q1/Q2 submission. Pricing is deliberately omitted until verified against provider pricing in effect at execution time.
