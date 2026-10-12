"""Immutable records of the Q1 pilot: issues and their outcomes, each written once (standard library only).

A record is a file {"meta": ..., "payload": ...}. The payload is canonical JSON (sorted keys, no floats, UTF-8); its
SHA-256 is kept in the meta, which also says when and by which code the record was written.

- An issue is written by an exclusive create: the finished bytes go to a temporary file that is then hard-linked under
  its final name, which fails if the name exists. There is never a partial file and never an overwrite. The same
  issue_id with the same payload is an idempotent access (nothing is written, the original meta stays); the same
  issue_id with a different payload is a collision: refused, the existing bytes untouched.
- An outcome is a separate file linked to one issue by its issue_id and the SHA-256 of that issue's payload. Attaching
  or correcting an outcome never opens an issue file for writing. A correction is a new outcome record
  (revision + 1, supersedes = the previous outcome_id); the previous one stays.
- Files are made read-only after writing. Windows refuses ordinary writes to them; this is a guard against accidents,
  not a proof against a determined person. Detection of such a change is verify(): every payload hash, every identity,
  every outcome's link to the issue bytes it was attached to.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import stat
import uuid
from pathlib import Path

ISSUE_KIND = "SIMULATED_ISSUE"     # a historical replay made now; ACTUALLY_DISPLAYED_ISSUE is reserved for a live answer


class Collision(Exception):
    """A different payload under an existing identity."""


# ---------- canonical bytes and identities (the one recipe the engine and verify() share) ----------
def canonical(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(obj) -> str:
    return hashlib.sha256(obj if isinstance(obj, (bytes, bytearray)) else canonical(obj)).hexdigest()


def target_id(target: dict) -> str:
    """The target: session + question version + its measuring frame + the place and side + the absolute horizon. The
    cut, the estimator and the history used are not part of it (Q1 §4)."""
    return sha(["q1-target-1", target])


def issue_id(target_id_: str, cut_index: int, estimator: str, model: str, input_digest: str, kind: str = ISSUE_KIND) -> str:
    """One issue = one target, one cut, one estimator, one model version, one input snapshot, one kind (Q1 §4)."""
    return sha(["q1-issue-1", target_id_, int(cut_index), estimator, model, input_digest, kind])


def outcome_id(issue_id_: str, observed: dict, basis: dict, revision: int, supersedes) -> str:
    return sha(["q1-outcome-1", issue_id_, observed, basis, int(revision), supersedes])


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# ---------- the store ----------
class Store:
    def __init__(self, root):
        self.root = Path(root)
        for kind in ("issues", "outcomes"):
            (self.root / kind).mkdir(parents=True, exist_ok=True)

    # -- writing once
    def _write_once(self, kind: str, rid: str, payload: dict, meta: dict):
        folder = self.root / kind
        final = folder / f"{rid}.json"
        body = canonical(payload)
        if final.exists():
            old = json.loads(final.read_text(encoding="utf-8"))
            if canonical(old["payload"]) == body:
                return "IDEMPOTENT", old
            raise Collision(f"{kind[:-1]} {rid}: a different payload under an existing identity; the stored record is kept")
        rec = {"meta": dict(meta, payload_sha256=sha(body)), "payload": payload}
        data = canonical(rec) + b"\n"
        tmp = folder / f".tmp-{rid[:16]}-{uuid.uuid4().hex}"
        with open(tmp, "xb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        try:
            try:
                os.link(tmp, final)                       # atomic; refuses an existing name
            except FileExistsError:
                return self._write_once(kind, rid, payload, meta)   # written meanwhile: compare, never overwrite
            except OSError:                               # no hard links on this file system: exclusive open instead
                fd = os.open(final, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0))
                with os.fdopen(fd, "wb") as f:
                    f.write(data)
        finally:
            if tmp.exists():
                os.remove(tmp)
        os.chmod(final, stat.S_IREAD)
        return "CREATED", rec

    def put_issue(self, payload: dict, meta: dict | None = None):
        rid = payload["issue_id"]
        expect = issue_id(payload["target_id"], payload["cut"]["index"], payload["estimator"]["id"],
                          payload["inputs"]["model"], payload["inputs"]["input_digest"], payload["issue_kind"])
        if rid != expect or payload["target_id"] != target_id(payload["target"]):
            raise ValueError("issue payload: identity fields do not produce its issue_id / target_id")
        base = dict(record="Q1_ISSUE", created_utc=utc_now(),
                    outcomes_on_record_for_target=len(self.outcomes(target_id_=payload["target_id"])))
        return self._write_once("issues", rid, payload, dict(base, **(meta or {})))

    def put_outcome(self, payload: dict, meta: dict | None = None):
        rid = payload["outcome_id"]
        if rid != outcome_id(payload["issue_id"], payload["observed"], payload["basis"], payload["revision"], payload["supersedes"]):
            raise ValueError("outcome payload: identity fields do not produce its outcome_id")
        issue = self.get_issue(payload["issue_id"])
        if issue is None:
            raise ValueError("outcome without its issue")
        if issue["meta"]["payload_sha256"] != payload["issue_payload_sha256"] or sha(issue["payload"]) != payload["issue_payload_sha256"]:
            raise ValueError("outcome: the issue's bytes differ from the ones it is linked to")
        base = dict(record="Q1_OUTCOME", created_utc=utc_now())
        return self._write_once("outcomes", rid, payload, dict(base, **(meta or {})))

    # -- reading
    @staticmethod
    def _load(p: Path):
        return json.loads(p.read_text(encoding="utf-8"))

    def get_issue(self, rid: str):
        p = self.root / "issues" / f"{rid}.json"
        return self._load(p) if p.exists() else None

    def get_outcome(self, rid: str):
        p = self.root / "outcomes" / f"{rid}.json"
        return self._load(p) if p.exists() else None

    def issues(self, target_id_: str | None = None):
        out = [self._load(p) for p in sorted((self.root / "issues").glob("*.json"))]
        return [r for r in out if target_id_ is None or r["payload"]["target_id"] == target_id_]

    def outcomes(self, issue_id_: str | None = None, target_id_: str | None = None):
        out = [self._load(p) for p in sorted((self.root / "outcomes").glob("*.json"))]
        return [r for r in out if (issue_id_ is None or r["payload"]["issue_id"] == issue_id_)
                and (target_id_ is None or r["payload"]["target_id"] == target_id_)]

    def raw_bytes(self, kind: str, rid: str) -> bytes:
        return (self.root / kind / f"{rid}.json").read_bytes()

    # -- verification
    def verify(self):
        """Recompute every payload hash and identity; check that every outcome still points at the issue bytes it was
        attached to; report files that are no longer read-only."""
        rep = dict(issues=0, outcomes=0, problems=[], writable=[])
        current = {}
        for p in sorted((self.root / "issues").glob("*.json")):
            rep["issues"] += 1
            try:
                rec = self._load(p)
                pl = rec["payload"]
                h = sha(pl)
                current[pl["issue_id"]] = h
                if h != rec["meta"]["payload_sha256"]: rep["problems"].append(f"issue {p.stem}: payload hash differs from its meta")
                if p.stem != pl["issue_id"]: rep["problems"].append(f"issue {p.stem}: file name differs from issue_id")
                if pl["target_id"] != target_id(pl["target"]): rep["problems"].append(f"issue {p.stem}: target_id differs from its target")
                if pl["issue_id"] != issue_id(pl["target_id"], pl["cut"]["index"], pl["estimator"]["id"], pl["inputs"]["model"],
                                              pl["inputs"]["input_digest"], pl["issue_kind"]):
                    rep["problems"].append(f"issue {p.stem}: issue_id differs from its identity fields")
            except Exception as exc:                       # an unreadable record is a finding, not a crash
                rep["problems"].append(f"issue {p.stem}: unreadable ({exc})")
            if os.access(p, os.W_OK): rep["writable"].append(p.name)
        for p in sorted((self.root / "outcomes").glob("*.json")):
            rep["outcomes"] += 1
            try:
                rec = self._load(p)
                pl = rec["payload"]
                if sha(pl) != rec["meta"]["payload_sha256"]: rep["problems"].append(f"outcome {p.stem}: payload hash differs from its meta")
                if pl["outcome_id"] != outcome_id(pl["issue_id"], pl["observed"], pl["basis"], pl["revision"], pl["supersedes"]):
                    rep["problems"].append(f"outcome {p.stem}: outcome_id differs from its identity fields")
                if pl["issue_id"] not in current: rep["problems"].append(f"outcome {p.stem}: its issue is missing")
                elif current[pl["issue_id"]] != pl["issue_payload_sha256"]:
                    rep["problems"].append(f"outcome {p.stem}: the issue changed after this outcome was attached")
            except Exception as exc:
                rep["problems"].append(f"outcome {p.stem}: unreadable ({exc})")
            if os.access(p, os.W_OK): rep["writable"].append(p.name)
        rep["ok"] = not rep["problems"]
        return rep
