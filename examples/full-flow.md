# ORRO Full Flow

This example uses the current witnessd-hosted `orro` command. It does not require a standalone ORRO package.

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .

orro init --home .witnessd --depone-root ../Depone
orro doctor --home .witnessd --json
orro engine-lock --home .witnessd --out .witnessd/orro-engine-lock.json

orro advise "fix parser bug" --repo . --home .witnessd --json
orro scout "fix parser bug" --repo . --home .witnessd
orro flowplan "fix parser bug" \
  --root . \
  --profile code-change \
  --out .witnessd/workflow-plan.json \
  --role-lanes-out .witnessd/role-lane-plan.json

orro proofrun "fix parser bug" \
  --repo . \
  --home .witnessd \
  --workflow-plan .witnessd/workflow-plan.json \
  --role-lane-plan .witnessd/role-lane-plan.json

orro next .witnessd/runs/<run-dir> --home .witnessd --json
orro proofcheck .witnessd/runs/<run-dir> \
  --home .witnessd \
  --out .witnessd/runs/<run-dir>/proofcheck-verdict.json
orro handoff .witnessd/runs/<run-dir> \
  --out .witnessd/runs/<run-dir>/orro-handoff.json
orro report .witnessd/runs/<run-dir> --home .witnessd
```

`proofcheck` must pass before formal handoff. Handoff is review packaging, not approval. Report is summary, not proof.
