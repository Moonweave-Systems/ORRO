"use strict";

// ORRO — Observed Run & Review Orchestrator (Moonweave).
// Name placeholder. Active product: https://github.com/Moonweave-Systems/ORRO

const PROJECT_URL = "https://github.com/Moonweave-Systems/ORRO";

function about() {
  return (
    "ORRO — Observed Run & Review Orchestrator (Moonweave).\n" +
    "Evidence-backed execution layer for coding agents: scout -> flowplan -> " +
    "proofrun -> proofcheck -> handoff.\n" +
    "Project: " + PROJECT_URL
  );
}

module.exports = { version: "0.0.1", PROJECT_URL, about };
