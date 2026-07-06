# Install

Current development layout uses the engine repositories directly:

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .
orro init --home .witnessd --depone-root ../Depone
```

The `orro` command is currently implemented by witnessd. This repository is a
product/distribution skeleton and does not publish a standalone package yet.

Future packaging should provide one user-facing ORRO install with pinned Depone
and witnessd engine versions.
