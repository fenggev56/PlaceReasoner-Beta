"""macroflow - structured multi-agent macro-placement flow.

Design split:

* LLM agents (Planner / Placer / Checker) make design decisions: macro
  strategy, placement shape, gate verdicts and revisions.
* Python modules handle system operations: OpenROAD process control,
  deterministic geometry, legalization, metric parsing, OpenROAD image capture,
  candidate bookkeeping, telemetry and TCL rendering.

The orchestrator runs init and macro placement (Gate A), then the fixed
detail-place -> CTS -> route skill templates to obtain routed PPA feedback.
Only the macro placement is optimized; downstream stages are never tuned.

This package is self-contained: it does not depend on any other agent
framework. Sub-modules import lazily so the pure system-operation layer
can be tested without loading torch or starting OpenROAD.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
