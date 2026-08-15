# 🚀 AGX — Antigravity Unified Management Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-brightgreen.svg)](https://python.org)
[![CLI: Typer](https://img.shields.io/badge/CLI-Typer-red.svg)](https://typer.tiangolo.com)

**AGX** (`agx`) is the ultimate CLI & IDE management suite for Google Antigravity. It enables bidirectional conversation synchronization, trajectory diffing, workspace migration, automated backups, duplicate session detection, and diagnostic health checks between Antigravity CLI and Antigravity IDE.

---

## ⚡ Key Features

- 🔄 **Unified Index Synchronization**: Keeps CLI SQLite indexes and IDE Protobuf global state in perfect harmony.
- 🚀 **One-Command Auto Restart (`agx sync -r`)**: Gracefully flushes WAL caches, synchronizes state, and relaunches the IDE.
- 📊 **Analytics Dashboard (`agx stats`)**: Visualizes conversation distributions, step counts, and active workspaces with rich terminal charts.
- 🔍 **Full-Text Search (`agx search <query>`)**: Instant search across titles, UUIDs, and deep transcript logs.
- 🔀 **Trajectory Diffing (`agx diff <id1> <id2>`)**: Compare conversation lengths, user prompt sequences, and turns side-by-side.
- 🧹 **Orphan & Duplicate Cleanup (`agx prune`, `agx dedup`)**: Detects and purges dangling `.tmp` files and duplicate sessions.
- 📂 **Workspace Migration (`agx rebind <old> <new>`)**: Batch re-indexes conversations when repositories or folders move on disk.
- 💾 **Full State Snapshots (`agx backup`, `agx restore`)**: Bundles brains, SQLite databases, and global state into compressed `.tar.gz` archives.
- 🩺 **Diagnostic Health Check (`agx doctor`)**: Verifies symlink health, database integrity (`PRAGMA integrity_check`), and version compatibility.
- 👁️ **Live Watcher Daemon (`agx watch`)**: Continuous background synchronization as turns execute.

---

## 📦 Installation

### Using `uv` (Recommended)

```bash
# Clone the repository
git clone https://github.com/hardik88t/agx.git
cd agx

# Install tool in user environment
uv tool install .
```

### Updating & Development Installation

```bash
# Install / Reinstall globally from local repo
uv tool install --reinstall .

# Editable live development mode (source edits take effect immediately)
uv tool install --editable . --force

# Shell autocompletion setup
agx --install-completion bash  # or zsh / fish
```

---

## 🛠️ Command Reference

| Command | Description |
|---|---|
| `agx` | Display help and list all available subcommands |
| `agx sync` | Run default bidirectional index synchronization |
| `agx sync -r` | Terminate IDE, sync database, and relaunch IDE |
| `agx list [-n 25] [-w <uri>]` | Formatted conversation history table |
| `agx search <query>` | Full-text search across conversations and transcripts |
| `agx stats` | View workspace analytics and token step distributions |
| `agx diff <id1> <id2>` | Compare two conversation trajectories side-by-side |
| `agx dedup [--apply]` | Scan and clean duplicate sessions |
| `agx rebind <old> <new>` | Rebind project path URIs when moving repositories |
| `agx prune` | Clean orphaned records and dangling `.tmp` files |
| `agx backup [-o <path>]` | Create timestamped `.tar.gz` state snapshot |
| `agx restore <path>` | Rollback from a state backup archive |
| `agx export <id> [-o <file.md>]` | Export conversation transcript to clean Markdown |
| `agx doctor` | Run diagnostic health check |
| `agx watch [--interval 5]` | Run background auto-sync watcher daemon |
| `agx config init [--force]` | Initialize `$XDG_CONFIG_HOME/agx/config.toml` |
| `agx config show` | View active config path and file contents |

---

## ⚙️ Configuration (XDG Base Directory)

AGX follows the XDG Base Directory Specification. Configuration is read from:
- **Config**: `$XDG_CONFIG_HOME/agx/config.toml` (default: `~/.config/agx/config.toml`)
- **Backups**: `$XDG_DATA_HOME/agx/backups/` (default: `~/.local/share/agx/backups/`)

Initialize a configuration file with:
```bash
agx config init
```

You can also override settings via environment variables:

| Environment Variable | Default Value | Purpose |
|---|---|---|
| `AGX_TARGET_CLI_VERSION` | `1.1.13` | Target Antigravity CLI version lock |
| `AGX_TARGET_IDE_VERSION` | `2.5.5` | Target Antigravity IDE version lock |
| `AGX_GEMINI_DIR` | `~/.gemini` | Root Gemini Antigravity data folder |
| `AGX_CLI_DIR` | `~/.gemini/antigravity-cli` | Antigravity CLI directory |
| `AGX_IDE_DIR` | `~/.gemini/antigravity-ide` | Antigravity IDE directory |
| `AGX_IDE_STATE_DB` | OS-specific `state.vscdb` | Global VSCode/Electron state SQLite DB |

---

## 📄 License

MIT License. Developed for the Antigravity developer community.
