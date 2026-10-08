"""Faceless Fleet — a review-gated, config-driven pipeline for ambient/sleep
faceless YouTube channels.

Division of labor (per the research playbook):
  - Claude Code / MCP = builder + generation touchpoint + scheduled review
  - deterministic Python (assemble/upload/schedule) = the unattended loop
  - one human quality gate sits between pending_review/ and approved/
"""

__version__ = "0.1.0"
