# Code

Two environments, both Python/uv. `study/` runs the stated-plan grid (scores summaries); `live/` runs
the executed-RCE tests (real commands in a Docker sandbox). `live/` imports the harness from
`study/src` and reuses the pinned prompts in `prompts/`.

| Path       | What it is                                                                         |
| ---------- | ---------------------------------------------------------------------------------- |
| `study/`   | the `compaction_study` package — serializers, canaries, scoring, providers, CLI    |
| `live/`    | executed-RCE runners (real agent loop + `docker exec`)                             |
| `prompts/` | pinned upstream compaction prompts + `PROVENANCE.md` + `refresh.sh` (load-bearing) |

## Script → experiment → result

| Run                                                          | Experiment                                     | Produces                                   |
| ------------------------------------------------------------ | ---------------------------------------------- | ------------------------------------------ |
| `cd study && uv run study t1 --replicates 8`                 | E1/E2/E3 laundering + ablation                 | `data/stated-plan/t1_*`                    |
| `cd study && uv run study t2 --rounds 5 --replicates 3`      | E4 ratchet                                     | `data/stated-plan/t2_*`                    |
| `cd study && uv run study t3 --input <t1.jsonl>`             | E9 defense (re-analysis, no API)               | `data/stated-plan/t3_*`                    |
| `cd study && uv run study t4`                                | E5 behavioral (stated plan)                    | `data/stated-plan/t4_*`                    |
| `cd live && uv run python run_live.py --scale 25 --reps 3`   | E6 executed RCE, cross-model                   | `data/live/live_result.json`               |
| `cd live && uv run python run_matrix.py --scale 25 --reps 3` | E6 executed RCE, harness × scenario            | `data/live/matrix_result.json`             |
| `cd live && uv run python run_execute_scale.py`              | E6 executed rate vs context size               | `data/live/execute_scale_result.json`      |
| `cd live && uv run python run_control_arms.py`               | E6 control: forged vs genuine vs clean         | `data/live/control_arms_result.json`       |
| `cd live && uv run python run_context_scale.py`              | E7 laundering vs context size                  | `data/live/context_scale_result.json`      |
| `cd live && uv run python run_position_scale.py`             | E8 laundering vs poison position               | `data/live/position_scale_result.json`     |
| `cd live && uv run python run_flattening.py`                 | E10 laundering across flattening harnesses     | `data/live/flattening_result.json`         |
| `cd live && uv run python run_structured.py`                 | E10 structured control (0% launder)            | `data/live/structured_result.json`         |
| `cd live && uv run python judge_rescore.py`                  | E10 LLM-judge scoring of both                  | `data/live/judged_result.json`             |
| `cd live && uv run python run_execute_flattening.py`         | E11 executed RCE on 4 new flattening harnesses | `data/live/execute_flattening_result.json` |
| `cd live && uv run python run_context_scale_1m.py`           | E12 laundering out to the ~908k ceiling        | `data/live/context_scale_1m_result.json`   |
| `cd live && uv run python run_salience_recovery.py`          | E13 salience→execution + attacker override     | `data/live/salience_recovery_result.json`  |
| `cd live && uv run python run_salience_scale.py`             | E14 salience declines with window size         | `data/live/salience_scale_result.json`     |
| `cd code/figures && uv run python make_figures.py`           | regenerate paper figures from the JSONs        | `figures/fig{1..4}-*.{pdf,svg,png}`        |
| `cd live && uv run python capture_evidence.py`               | verbatim pivotal-turn capture                  | `data/live/evidence.json`                  |

## Notes

- **Keys.** `study` needs `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and a GLM key; restrict families with
  `--families anthropic openai`. `live` uses `OPENAI_API_KEY`.
- **`--scale` (live runners)** sets how big the surrounding session is: `0` = a short toy transcript,
  `25` ≈ a realistic ~26k-token session (the executed ceiling), `260` ≈ a full ~300k-token window. The
  filler is a coherent env/build-troubleshooting session so the laundered "bootstrap approved" line has
  a task to act on. `run_execute_scale.py` sweeps sizes on its own.
- **Prompts load at import time** from `prompts/`. Re-run `prompts/refresh.sh` before any number goes
  public — upstream prompts change often; `prompts/PROVENANCE.md` records the pinned commits.
- **Scoring is deterministic.** Metric changes re-apply to stored JSONL for free — never re-run a grid
  to fix a metric.
- **Live runners write results next to themselves** (`live/*.json`); the committed snapshot lives in
  `data/live/`. Copy a fresh run over if you want to update the snapshot.
- **Safety.** `live` executes model-emitted commands inside a disposable `docker run --rm` alpine
  container, scratch dir only, attacker server on localhost, benign proof-file payload.
- **Figures.** `code/figures/` is a small uv project (matplotlib). `make_figures.py` reads
  `data/live/*.json` and writes `figures/figN-*.{pdf,svg,png}` deterministically from one shared
  style block — the PDF (fonts embedded) is what the paper embeds, the SVG (text outlined) is for the
  Markdown/site, the PNG is a preview. Regenerate after any data refresh and commit the
  results; `make_figures.py --check` fails if the committed figures no longer match the data.
