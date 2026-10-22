# macroflow - structured multi-agent macro-placement flow

`macroflow` is the macro-placement system behind `run_flow.py`. LLM agents
make placement decisions; Python handles OpenROAD execution, legalization,
metrics, snapshots, candidate storage and telemetry.

Only the macro placement is optimized. Detailed placement, CTS and routing run
the fixed `skills/skills_Nangate45` templates purely to obtain routed PPA
feedback for each candidate.

## Agents

| Agent | Responsibility |
|---|---|
| Planner | Reads the floorplan image, macro list, cluster file and region grid; proposes a macro-placement strategy (shape / topology). |
| Placer | Converts the strategy into `#index -> (x, y, orient)` coordinates (`vlm_place_coords: true`) or a region-count distribution. |
| Checker | Gate A: judges the pin-side-highlighted macro-placement image, returns PASS/FAIL, `proceed`, and executable feedback for the Placer. |
| Optimizer | After routing: proposes new strategies for the best candidate from its routed PPA + images (skill `5.optimizer`). |

Every layout image is produced by OpenROAD `save_image` through `ORSession`.

## Flow

```text
init
  Python renders/sources floorplan.tcl (reads the predefined floorplan DEF),
  writes floorplan.odb, saves the initial image, and extracts core bounds,
  macro sizes and pin boxes.

macro candidate batch (one isolated worker process per candidate)
  Planner creates a distinct macro shape/topology strategy.
  Placer places macros; Python legalizes (legalize.py) and places in batches.
  Gate A loop (<= gate_a_max_refine):
    pin-side image -> Checker; on FAIL the Placer refines the current
    placement (Planner is not re-run). On limit, continue with the latest.
  detail_place.tcl   (fixed)
  cts_route.tcl / cts_route_light.tcl   (fixed, route_mode)
  save candidate: coords, gate verdicts, routed PPA, images, ODBs.

post-route optimization loops (<= post_route_opt_loops)
  pick the global best by routed timing;
  optimizer_variants variants = Optimizer strategies + geometric local moves;
  each variant goes through the same fixed backend;
  stop when no variant beats the best or the design's TNS goal is met.
```

## Parallel Candidates

`flow.macro_candidates` controls how many macro-placement candidates are
generated; `flow.parallel_workers` controls parallelism. The parent process
seeds `n` distinct shape strategies, then launches isolated worker processes
(own work directory, generated scripts, OpenROAD session and LLM client).
Worker results are merged into `<work-dir>/candidates/`. Process-level
parallelism is deliberate: OpenROAD sessions are stateful and must not share
a live design database.

## Config Knobs

In `config.yaml`:

```yaml
flow:
  macro_candidates: 5
  parallel_workers: 5
  gate_a_max_refine: 4
  vlm_place_coords: true
  post_route_opt_loops: 2
  optimizer_variants: 4
  route_mode: timing
```

CLI overrides: `--macro-candidates`, `--parallel-workers`,
`--gate-a-max-refine`, `--post-route-opt-loops`, `--route-mode`.

## Artifacts

```text
<work-dir>/candidates/                    merged candidate ledger (+ index.json)
<work-dir>/candidate_workers/cand_NN/     per-worker isolated runs
<work-dir>/post_route_workers/loop_NN/    optimizer-loop variants
<work-dir>/images/                        init / macro / pin-side / detail / routed snapshots
<work-dir>/saves_db/                      ODB checkpoints
<work-dir>/report/                        detail-place + CTS/route logs and reports
<work-dir>/model_output/run/summary.txt
<work-dir>/model_output/run/telemetry.json
```

## Self-test

```bash
python -m macroflow.selftest      # fake LLM + fake OpenROAD, no API calls
```
