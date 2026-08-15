"""
Configuration & Dynamic Path Resolution
========================================
Resolves system paths dynamically without hardcoded personal usernames.
Supports Linux, macOS, and Windows.
Configurable via environment variables and optional configuration file.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

# ─── Platform Detection ───────────────────────────────────────────────
IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

HOME = Path.home()

# ─── XDG Base Directory Resolution ────────────────────────────────────
XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share"))
XDG_STATE_HOME = Path(os.environ.get("XDG_STATE_HOME", HOME / ".local" / "state"))
XDG_CACHE_HOME = Path(os.environ.get("XDG_CACHE_HOME", HOME / ".cache"))

AGX_CONFIG_DIR = XDG_CONFIG_HOME / "agx"
AGX_DATA_DIR = XDG_DATA_HOME / "agx"
AGX_STATE_DIR = XDG_STATE_HOME / "agx"

CONFIG_FILE = AGX_CONFIG_DIR / "config.toml"


def _load_toml_config() -> dict:
    """Load configuration from XDG config.toml if present."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        if sys.version_info >= (3, 11):
            import tomllib
            with open(CONFIG_FILE, "rb") as f:
                return tomllib.load(f)
        else:
            try:
                import tomli as tomllib
                with open(CONFIG_FILE, "rb") as f:
                    return tomllib.load(f)
            except ImportError:
                return {}
    except Exception:
        return {}


USER_CONFIG = _load_toml_config()

# ─── Target Version Locks ─────────────────────────────────────────────
DEFAULT_TARGET_CLI_VERSION = "1.1.13"
DEFAULT_TARGET_IDE_VERSION = "2.5.5"

TARGET_CLI_VERSION = os.environ.get(
    "AGX_TARGET_CLI_VERSION",
    USER_CONFIG.get("versions", {}).get("target_cli_version", DEFAULT_TARGET_CLI_VERSION),
)
TARGET_IDE_VERSION = os.environ.get(
    "AGX_TARGET_IDE_VERSION",
    USER_CONFIG.get("versions", {}).get("target_ide_version", DEFAULT_TARGET_IDE_VERSION),
)


def _resolve_ide_app_dir() -> Optional[Path]:
    """Find the Antigravity IDE application resources directory."""
    if "ide_app_dir" in USER_CONFIG.get("paths", {}):
        p = Path(USER_CONFIG["paths"]["ide_app_dir"])
        if p.exists():
            return p

    candidates = []
    if IS_LINUX:
        candidates.extend([
            HOME / "Applications" / "Antigravity IDE",
            HOME / "Applications" / "Antigravity",
            Path("/opt/antigravity-ide"),
            Path("/usr/share/antigravity-ide"),
            HOME / ".local" / "share" / "antigravity-ide",
        ])
    elif IS_MAC:
        candidates.extend([
            Path("/Applications/Antigravity IDE.app"),
            Path("/Applications/Antigravity.app"),
            HOME / "Applications" / "Antigravity IDE.app",
            HOME / "Applications" / "Antigravity.app",
        ])
    elif IS_WINDOWS:
        local_app = Path(os.environ.get("LOCALAPPDATA", HOME / "AppData" / "Local"))
        prog_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        candidates.extend([
            local_app / "Programs" / "Antigravity IDE",
            local_app / "Programs" / "Antigravity",
            local_app / "Antigravity IDE",
            local_app / "Antigravity",
            prog_files / "Antigravity IDE",
            prog_files / "Antigravity",
        ])

    for c in candidates:
        if c.exists():
            return c
    return candidates[0] if candidates else None


def _resolve_ide_executable() -> Optional[str]:
    if "ide_executable" in USER_CONFIG.get("paths", {}):
        return USER_CONFIG["paths"]["ide_executable"]
    app_dir = _resolve_ide_app_dir()
    if not app_dir:
        return "antigravity-ide"
    if IS_MAC:
        return str(app_dir)
    if IS_WINDOWS:
        for exe_name in ["Antigravity IDE.exe", "Antigravity.exe", "antigravity-ide.exe"]:
            exe = app_dir / exe_name
            if exe.exists():
                return str(exe)
        return "Antigravity IDE.exe"
    exe = app_dir / "antigravity-ide"
    return str(exe) if exe.exists() else "antigravity-ide"


def _resolve_ide_state_db() -> Path:
    if "AGX_IDE_STATE_DB" in os.environ:
        return Path(os.environ["AGX_IDE_STATE_DB"])
    if "ide_state_db" in USER_CONFIG.get("paths", {}):
        return Path(USER_CONFIG["paths"]["ide_state_db"])
    if IS_MAC:
        for folder in ["Antigravity IDE", "Antigravity"]:
            p = HOME / "Library" / "Application Support" / folder / "User" / "globalStorage" / "state.vscdb"
            if p.exists():
                return p
        return HOME / "Library" / "Application Support" / "Antigravity IDE" / "User" / "globalStorage" / "state.vscdb"
    if IS_WINDOWS:
        appdata = Path(os.environ.get("APPDATA", HOME / "AppData" / "Roaming"))
        for folder in ["Antigravity IDE", "Antigravity"]:
            p = appdata / folder / "User" / "globalStorage" / "state.vscdb"
            if p.exists():
                return p
        return appdata / "Antigravity IDE" / "User" / "globalStorage" / "state.vscdb"
    for folder in ["Antigravity IDE", "antigravity-ide", "Antigravity"]:
        p = XDG_CONFIG_HOME / folder / "User" / "globalStorage" / "state.vscdb"
        if p.exists():
            return p
    return XDG_CONFIG_HOME / "Antigravity IDE" / "User" / "globalStorage" / "state.vscdb"


def format_workspace_uri(uri: str) -> str:
    """Format and shorten a workspace URI for clean display across platforms."""
    if not uri:
        return ""
    raw = uri
    if raw.startswith("file://"):
        raw = raw[7:]
    raw = unquote(raw)
    try:
        p = Path(raw)
        home_str = str(HOME)
        if str(p) == home_str:
            return "~"
        if str(p).startswith(home_str + "/") or str(p).startswith(home_str + "\\"):
            return "~" + str(p)[len(home_str):]
        return str(p)
    except Exception:
        return raw


# ─── Config Paths ──────────────────────────────────────────────────────
IDE_APP_DIR = _resolve_ide_app_dir()
IDE_PRODUCT_JSON = (IDE_APP_DIR / "resources" / "app" / "product.json") if IDE_APP_DIR else None
IDE_EXECUTABLE = _resolve_ide_executable()
IDE_STATE_DB = _resolve_ide_state_db()

_paths_cfg = USER_CONFIG.get("paths", {})
GEMINI_DIR = Path(os.environ.get("AGX_GEMINI_DIR", _paths_cfg.get("gemini_dir", HOME / ".gemini")))
CLI_DIR = Path(os.environ.get("AGX_CLI_DIR", _paths_cfg.get("cli_dir", GEMINI_DIR / "antigravity-cli")))
IDE_DIR = Path(os.environ.get("AGX_IDE_DIR", _paths_cfg.get("ide_dir", GEMINI_DIR / "antigravity-ide")))

CLI_SUMMARIES_DB = Path(os.environ.get("AGX_CLI_SUMMARIES_DB", _paths_cfg.get("cli_summaries_db", CLI_DIR / "conversation_summaries.db")))
CONVS_DIR = Path(os.environ.get("AGX_CONVS_DIR", _paths_cfg.get("convs_dir", IDE_DIR / "conversations")))
BRAIN_DIR = Path(os.environ.get("AGX_BRAIN_DIR", _paths_cfg.get("brain_dir", IDE_DIR / "brain")))
BACKUP_DIR = Path(os.environ.get("AGX_BACKUP_DIR", _paths_cfg.get("backup_dir", AGX_DATA_DIR / "backups")))


def get_ide_version() -> Optional[str]:
    if not IDE_PRODUCT_JSON or not IDE_PRODUCT_JSON.exists():
        return None
    try:
        with open(IDE_PRODUCT_JSON, "r", encoding="utf-8") as f:
            return json.load(f).get("ideVersion")
    except Exception:
        return None


def get_cli_version() -> Optional[str]:
    log_dir = CLI_DIR / "log"
    if not log_dir.exists():
        return None
    log_files = list(log_dir.glob("cli-*.log"))
    if not log_files:
        return None
    log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        with open(log_files[0], "r", errors="ignore", encoding="utf-8") as f:
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                import re
                match = re.search(r"Language server version:\s*([0-9.]+)", line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return None
