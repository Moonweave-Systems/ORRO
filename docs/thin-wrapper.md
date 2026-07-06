# ORRO Thin Wrapper

Depone verifies; witnessd executes; ORRO exposes the workflow.

The thin wrapper skeleton is the first executable wrapper surface in this
repository. It is intentionally narrow: it reports ORRO wrapper boundaries and
delegates explicit commands to the existing witnessd-hosted `orro` command.

The wrapper is not proof, not verifier truth, not package publish, not approval,
and not assurance.

## Command

The package exposes `orro-wrapper`, not `orro`.

This is deliberate. The current `orro` command remains witnessd-hosted. The
wrapper does not shadow the witnessd-hosted `orro` command.

```bash
PYTHONPATH=src python3 -m orro_wrapper boundary
PYTHONPATH=src python3 -m orro_wrapper self-test
PYTHONPATH=src python3 -m orro_wrapper delegate -- --help
```

`delegate` forwards arguments to an existing engine command. By default that
command is the current Python interpreter running `-m orro`. Operators may
override it with `--engine-command` or `ORRO_ENGINE_COMMAND`.

## Boundary

The wrapper:

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

This skeleton is not a published ORRO package. Published ORRO package remains
future work.

Future package work must keep:

- pinned engine lock checks;
- bootstrap setup/fallback policy;
- pinned-engine e2e CI;
- no engine code in ORRO.

## Self-Test

The self-test does not call engine repositories:

```bash
PYTHONPATH=src python3 -m orro_wrapper self-test
```

It verifies the wrapper boundary, default delegation command parsing, and that
empty delegate invocations fail closed.

## Install Smoke

The local install smoke creates a temporary virtual environment, installs this
repository in editable mode, and verifies the installed `orro-wrapper` console
script:

```bash
python3 scripts/check_orro_wrapper_install.py --json
```

The install smoke checks that `orro-wrapper` is installed, that the package does
not install or shadow `orro`, that boundary and self-test commands pass, and
that explicit delegation works with a harmless Python command. It does not call
Depone or witnessd, does not run proofrun, does not run proofcheck, and does not
publish a package.

The install smoke result is setup/test metadata, not proof, not verifier truth,
not package publish, not approval, and not assurance.

## Distribution Smoke

The wrapper distribution smoke builds and installs a local wheel:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json
```

It verifies that the wheel contains wrapper modules only, exposes
`orro-wrapper`, does not expose or shadow `orro`, and contains no Depone,
witnessd, proofrun, proofcheck, scheduler, observer, fan-in, team-ledger, or
verifier implementation files.

The distribution smoke is local test metadata, not proof, not verifier truth,
not package publish, not approval, and not assurance. The current executable
`orro` command remains witnessd-hosted. Future migration to an ORRO-owned
`orro` command requires a separate migration wave.
