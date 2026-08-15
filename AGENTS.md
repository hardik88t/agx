# 🤖 AGENTS.md — Agent & Developer Operational Guardrails

This document outlines the architecture, invariants, development rules, and quality standards for AI coding agents and contributors working in this repository.

---

## 🏛️ Architecture Overview

AGX is structured as a modular Python package managed by `uv`:

```text
agx/
├── pyproject.toml         # Package definition (Hatchling backend, Typer + Rich)
├── src/
│   └── agx/
│       ├── config.py      # Dynamic cross-platform paths & environment overrides
│       ├── proto.py       # Pure Python Protobuf encoder/decoder & schema builder
│       ├── db.py          # SQLite connection helpers, timeouts & integrity checks
│       ├── main.py        # Typer CLI application entry point
│       ├── commands/      # Individual modular CLI command handlers
│       │   ├── sync.py    # Core Protobuf & SQLite index synchronization
│       │   ├── list_cmd.py# History listing & filtering
│       │   ├── search.py  # Full-text search
│       │   ├── diff.py    # Trajectory comparison
│       │   ├── stats.py   # Analytics & usage metrics
│       │   ├── dedup.py   # Duplicate thread detection
│       │   ├── rebind.py  # Workspace URI migrator
│       │   ├── prune.py   # Orphan record & temp file cleanup
│       │   ├── backup.py  # Snapshot backup & restore
│       │   ├── export.py  # Transcript to Markdown exporter
│       │   ├── doctor.py  # Diagnostic health checks
│       │   └── watch.py   # Background watcher daemon
│       └── utils/
│           ├── process.py # Process management (IDE kill & spawn)
│           └── transcript.py # Transcript log parsing & UUID resolution
```

---

## 🛡️ Critical Invariants & Rules [Update as per Development need]

1. **Zero Hardcoded Personal Paths**:
   - Never hardcode usernames, home paths (e.g. `/home/user`), or machine-specific mount points.
   - Always resolve via `agx.config.HOME` (`Path.home()`) or environment variables.

2. **Protobuf Binary Schema Compliance**:
   - The IDE global state (`state.vscdb` key `antigravityUnifiedStateSync.trajectorySummaries`) requires exact Protobuf fields:
     - **Field 1** (string): Title
     - **Field 2 / Field 16** (varint): Step Count
     - **Field 3 / 7 / 10** (message): Timestamps (google.protobuf.Timestamp: tag 1 = sec, tag 2 = nano)
     - **Field 4** (string UUID): Generator / Session ID
     - **Field 5** (varint): Mode (1)
     - **Field 9** (message): Workspace URI (`tag 1 = uri`, `tag 3 = ""`)
     - **Field 15** (string): Empty string `b""`
     - **Field 17** (message): Context blob (contains Field 9, Timestamp, Session UUID, CID, Workspace)
     - **Field 22** (varint): Category Enum (`4` = Chat / Cascade Trajectory).
   - Missing Field 22 or Field 9 causes the IDE sidebar parser to silently discard the conversation.

3. **Concurrency & Database Locks**:
   - Always connect to SQLite databases with `timeout=10.0` or open with `mode=ro` when reading.
   - When modifying `state.vscdb`, check if the IDE is running. If running, alert the user or require clean process termination before writing to prevent in-memory cache overwrite.

4. **Package Management (`uv`)**:
   - Use `uv` exclusively for dependency management and virtual environments.
   - Never commit `.venv/` or local `dist/` builds.

---

## 🧪 Testing Protocol

When adding new commands or modifying protobuf logic:
1. Run `uv run agx doctor` to verify system health.
2. Run `uv run agx --help` to confirm CLI interface parsing.
3. Run `uv run agx stats` to verify database connectivity.
4. Run `uv run agx list -n 5` to confirm history queries.
