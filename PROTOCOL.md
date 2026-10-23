# Experimental protocol — DRAFT, not preregistered

**Research question:** When do multi-agent orchestration patterns outperform a single-agent baseline in accuracy, latency, and token usage, and how does this depend on model/provider?

**No performance outcomes have been measured by this package's author.**

## Phase 1 — API pilot
- Public benchmark: GSM8K `openai/gsm8k`, configuration `main`, split `test`; fixed seed 42.
- Four architectures: single (1 request); sequential (4 requests); parallel (3 concurrent solver requests + coordinator); hierarchical (planner + 2 concurrent solvers + final coordinator).
- Three providers: OpenAI, Anthropic Claude, Google Gemini. Exact model IDs must be provided and logged.
- Pilot: 20 items, 1 repetition per model and architecture. Review failed requests and output parsing.

## Phase 2 — confirmatory (after pilot)
- Determine sample size by power or confidence-interval precision; freeze task IDs and full prompt templates.
- Fix model IDs, SDK versions, model settings, time period, concurrency, maximum output tokens, hardware/network, and pricing snapshots.
- Record dataset revision (current script does not pin it), SHA256, raw responses, API errors, UTC timestamps, and seeds.
- Primary outcome: exact numeric answer accuracy; secondary outcomes: end-to-end latency, token usage, request count, error rate, cost based on verified historical pricing.
- Analyze task-paired differences and 95% confidence intervals, with task/model clustering and multiple-comparison corrections.
- Conduct ablations on number of solver agents, coordinator, reviewer, parallelism, and token-matched single-agent baselines.
- Include additional domain benchmarks; GSM8K alone cannot justify general claims across domains or task complexity.

## Limitations and safeguards
- Multi-agent patterns use different numbers of API requests and context sizes; results are not a pure test of coordination.
- SDK token counters are provider-specific; missing values must remain missing.
- Numeric answer parsing is narrow and should be manually audited.
- No temperature override is used; model defaults and reasoning behavior can differ.
- No simulated outputs or fabricated metrics may be presented as empirical findings.
- Store credentials in environment variables; never commit `.env` or raw sensitive prompts.

## Phase 1b — second public benchmark (implemented)
- AI2 ARC-Challenge test split, original `allenai/ai2_arc` via Hugging Face.
- Independent question-level sampling without replacement; pin exact dataset repo SHA and SHA256 of selected CSV.
- Separate answer-label accuracy endpoint; GSM8K uses numeric exact match, ARC uses answer labels.
- Pre-specify difficulty stratification; dataset designation alone is not an empirical complexity metric.
- Budget-control matched single-agent and more diverse domains remain future work.
