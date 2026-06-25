"""Higgsfield generation client with two backends.

WHY TWO BACKENDS
----------------
The Higgsfield generation tools you have *today* are exposed as an MCP server
(auth = your Higgsfield account, billed in credits). MCP tools are callable by a
Claude Code / Cowork session — NOT by a standalone cron job. So:

  backend = "manifest"  (default, works today, MCP-only, no API key)
      generate.py writes a job manifest (jobs.json) describing exactly what to
      generate. A Claude Code session / Routine reads it, calls the Higgsfield
      MCP tools (generate_image -> generate_video -> generate_audio), and drops
      the resulting files into output/raw/<slug>/. This keeps Claude as the
      generation touchpoint, which the research recommends anyway.

  backend = "rest"  (fully unattended, needs HIGGSFIELD_API_KEY)
      Calls Higgsfield's HTTP API directly so a VPS/Actions cron can generate
      with no human/agent in the loop. Endpoint paths are stubbed below and
      flagged TODO — confirm them against Higgsfield's API docs before relying
      on this for blind automation.

Either way the *output contract* is identical: files land in output/raw/<slug>/
with predictable names, and assemble.py takes it from there.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class GenJob:
    """One unit of generation work, model-agnostic."""
    kind: str                       # "image" | "video" | "audio"
    model: str
    prompt: str
    out_name: str                   # filename to write under output/raw/<slug>/
    params: dict = field(default_factory=dict)
    input_media: str | None = None  # path/id of a start image for image->video
    status: str = "pending"         # pending | done | failed
    result_path: str | None = None


class HiggsfieldClient:
    def __init__(self, backend: str, raw_dir: Path):
        self.backend = backend
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.raw_dir / "jobs.json"

    # ---- manifest backend -------------------------------------------------
    def write_manifest(self, jobs: list[GenJob]) -> Path:
        payload = {
            "created_at": int(time.time()),
            "raw_dir": str(self.raw_dir),
            "instructions": (
                "Fulfill each pending job with the matching Higgsfield MCP tool "
                "(generate_image / generate_video / generate_audio), then download "
                "the result to raw_dir/out_name and set status=done, result_path. "
                "Do image jobs first; video jobs use the produced image as input_media."
            ),
            "jobs": [asdict(j) for j in jobs],
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2))
        return self.manifest_path

    def load_manifest(self) -> dict | None:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text())
        return None

    # ---- rest backend (unattended) ---------------------------------------
    def run_rest(self, jobs: list[GenJob]) -> list[GenJob]:
        api_key = os.environ.get("HIGGSFIELD_API_KEY")
        if not api_key:
            raise RuntimeError(
                "backend=rest needs HIGGSFIELD_API_KEY. Use backend=manifest until "
                "you have an API key, or fulfill the manifest via the MCP session."
            )
        import requests  # local import so manifest mode has no hard dep

        # TODO: confirm these against Higgsfield's official REST docs before trusting
        # in unattended mode. Shapes below are the conventional submit/poll pattern.
        base = os.environ.get("HIGGSFIELD_API_BASE", "https://api.higgsfield.ai/v1")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        for job in jobs:
            endpoint = {
                "image": "/images/generate",
                "video": "/videos/generate",
                "audio": "/audio/generate",
            }[job.kind]
            body = {"model": job.model, "prompt": job.prompt, **job.params}
            if job.input_media:
                body["image"] = job.input_media
            r = requests.post(base + endpoint, headers=headers, json=body, timeout=60)
            r.raise_for_status()
            task_id = r.json().get("id")
            url = self._poll_rest(base, headers, task_id)
            dest = self.raw_dir / job.out_name
            dest.write_bytes(requests.get(url, timeout=120).content)
            job.status, job.result_path = "done", str(dest)
        return jobs

    @staticmethod
    def _poll_rest(base, headers, task_id, tries=60, delay=5):
        import requests
        for _ in range(tries):
            r = requests.get(f"{base}/tasks/{task_id}", headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            if data.get("status") in ("completed", "succeeded", "done"):
                return data["result"]["url"]
            if data.get("status") in ("failed", "error"):
                raise RuntimeError(f"Higgsfield task {task_id} failed: {data}")
            time.sleep(delay)
        raise TimeoutError(f"Higgsfield task {task_id} did not finish")

    # ---- dispatch ---------------------------------------------------------
    def run(self, jobs: list[GenJob]) -> Path | list[GenJob]:
        if self.backend == "rest":
            return self.run_rest(jobs)
        return self.write_manifest(jobs)
