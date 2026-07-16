"""ORRO — the Observed Run & Review Orchestrator (Moonweave).

The ``orro`` command is a thin surface over the witnessd execution runtime and
the Depone verifier. This package owns the ``orro`` entry point and delegates
every command to the installed witnessd engine; it is not itself an execution
engine or verifier, and its own output is not proof or assurance.

Project: https://github.com/Moonweave-Systems/ORRO
"""

__version__ = "0.0.2"

PROJECT_URL = "https://github.com/Moonweave-Systems/ORRO"


def about() -> str:
    return (
        "ORRO — Observed Run & Review Orchestrator (Moonweave).\n"
        "Evidence-backed execution layer for coding agents: scout -> flowplan -> "
        "proofrun -> proofcheck -> handoff.\n"
        "The orro command delegates to the witnessd runtime; run `orro doctor` to "
        "check engine readiness.\n"
        f"Project: {PROJECT_URL}"
    )
