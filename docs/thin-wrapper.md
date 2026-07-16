# ORRO Thin Wrapper

Depone verifies; witnessd executes; ORRO exposes the workflow.

The thin wrapper is the executable ORRO product surface in this repository. It
is intentionally narrow: it reports ORRO wrapper boundaries and delegates engine
commands to the existing witnessd-hosted ORRO surface.

The wrapper is not proof, not verifier truth, not package publish, not approval,
and not assurance.

## Command

The package exposes the ORRO-owned `orro` command and keeps `orro-wrapper` as a
compatibility alias for the same wrapper module.

```bash
python3 -m pip install -e .
orro-wrapper boundary
orro boundary
orro-wrapper self-test
orro-wrapper delegate -- flowplan --help
```

`delegate` forwards arguments in-process to `witnessd.__main__.main`, prefixed
with the public `orro` command namespace. Normal ORRO commands use the same
in-process path after validation against `witnessd.__main__.ORRO_COMMANDS`.

## Boundary

The wrapper:

- owns the user-facing `orro` command;
- delegates to witnessd-hosted ORRO commands;
- contains no engine logic;
- does not implement proofrun;
- does not implement proofcheck;
- does not implement scheduler, observer, fan-in, team-lane, or team-ledger
  logic;
- does not verify evidence itself;
- does not approve merge;
- does not raise assurance.

When a delegated command runs proofrun or proofcheck, that behavior belongs to
the engine command the operator explicitly invoked. The wrapper only delegates.

## Relationship To Packaging

This repository contains the canonical publishable ORRO package metadata and
wrapper source. Published ORRO package remains future work because uploading it
to PyPI is a separate release step.

Future package work must keep:

- pinned engine lock checks;
- bootstrap setup/fallback policy;
- pinned-engine e2e CI;
- no engine code in ORRO.

## Self-Test

The self-test does not call engine repositories:

```bash
python3 -m pip install -e .
orro-wrapper self-test
```

It verifies the wrapper boundary and that empty delegate invocations fail
closed without invoking witnessd commands.

## Install Smoke

The local install smoke creates a temporary virtual environment, installs this
repository and its witnessd dependency in editable mode, and verifies the
installed `orro` and `orro-wrapper` console scripts:

```bash
python3 scripts/check_orro_wrapper_install.py --json
```

The install smoke checks that both commands are installed, that boundary and
self-test commands pass, and that explicit in-process delegation shows
witnessd's `flowplan --help`. It does not run proofrun, does not run proofcheck,
and does not publish a package.

The install smoke result is setup/test metadata, not proof, not verifier truth,
not package publish, not approval, and not assurance.

## Distribution Smoke

The wrapper distribution smoke builds and installs a local wheel:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json --allow-network
```

It verifies that the wheel contains wrapper modules only, exposes `orro` and
`orro-wrapper`, and contains no Depone, witnessd, proofrun, proofcheck,
scheduler, observer, fan-in, team-ledger, or verifier implementation files.
The explicit network flag authorizes pip provisioning for declared build and
runtime dependencies, including `witnessd>=2.3.2`.

The distribution smoke is local test metadata, not proof, not verifier truth,
not package publish, not approval, and not assurance.
