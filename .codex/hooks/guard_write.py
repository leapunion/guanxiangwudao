"""
PreToolUse hook: guard_write.py

Reads a Claude Code hook JSON payload from stdin.
Blocks Write/Edit operations to protected paths.
Enforces per-role write restrictions when CLAUDE_AGENT_ROLE is set.

Exit codes:
  0 - allow
  2 - block
"""

import json
import os
import pathlib
import sys
from fnmatch import fnmatch


# --------------------------------------------------------------------------- #
# Path rules
# --------------------------------------------------------------------------- #

# Paths that NO session (main or agent) may ever write.
# Narrow set: only truly sensitive artifacts (binary PRD, human-only inputs,
# packaging). Main session owns integration and may write src/data/schemas.
GLOBAL_DENY_PATTERNS = [
    "inputs/human/**",
    "docs/*.docx",
]

# Paths that sub-Agents (CLAUDE_AGENT_ROLE set) additionally may not write.
# Role agents work in their project subdirectory; integration code, master
# data and packaging config are off-limits for them.
AGENT_DENY_PATTERNS = [
    "data/**",
    "schemas/**",
    "src/**",
    "pyproject.toml",
    ".claude/agents/**",
    "CLAUDE.md",
    "AGENTS.md",
]

# Paths that ANY session (including the main session) may write.
ALLOW_PATTERNS = [
    "projects/**",
    "templates/**",
    "output/**",
    "tests/**",
    "assets/**",
    "docs/*.md",
    "docs/DEVLOG.md",
    ".claude/hooks/**",
    ".claude/skills/**",
    ".claude/rules/**",
    ".claude/settings.json",
    "CLAUDE.md",
    "AGENTS.md",
]

# Per-role additional write restrictions.
# When CLAUDE_AGENT_ROLE is set, the agent may ONLY write to paths matching
# its role pattern (plus the global ALLOW_PATTERNS minus DENY_PATTERNS).
ROLE_PATTERNS = {
    "classics-researcher": "projects/*/research/**",
    "ink-art-director": "projects/*/art/**",
    "independent-verifier": "projects/*/reviews/**",
}

# Tools that this hook inspects.
GUARDED_TOOLS = {"Write", "Edit"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _match(path, pattern):
    """Match a repo-relative path against a glob pattern.

    Handles two special cases:
    - Simple prefix `foo/**`  -> any path under foo/
    - Wildcard prefix `foo/*/bar/**` -> fnmatch on the non-** prefix segment,
      then require the rest exists.
    Anything else falls through to plain fnmatch.
    """
    path = path.lstrip("./").replace("\\", "/")
    pattern = pattern.lstrip("./")

    if pattern.endswith("/**"):
        prefix_pattern = pattern[:-3]   # e.g. "data" or "projects/*/research"
        prefix_parts = prefix_pattern.split("/")
        path_parts = path.split("/")
        n = len(prefix_parts)
        if len(path_parts) < n:
            return False
        path_prefix = "/".join(path_parts[:n])
        return fnmatch(path_prefix, prefix_pattern)

    return fnmatch(path, pattern)


def _matches_any(path, patterns):
    return any(_match(path, p) for p in patterns)


def _block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def _allow():
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)


def _to_repo_relative(file_path):
    """Return a repo-relative path string."""
    try:
        abs_path = pathlib.Path(file_path).resolve()
        cwd = pathlib.Path.cwd().resolve()
        return str(abs_path.relative_to(cwd)).replace("\\", "/")
    except ValueError:
        return file_path.lstrip("/").replace("\\", "/")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _block("guard_write: invalid JSON from stdin")

    tool_name = payload.get("tool_name", "")

    # Only guard Write and Edit.
    if tool_name not in GUARDED_TOOLS:
        _allow()

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path")

    if not file_path:
        _block("guard_write: Write/Edit called without file_path")

    norm = _to_repo_relative(file_path)

    agent_role = os.environ.get("CLAUDE_AGENT_ROLE", "").strip()

    # ----- Global deny check (applies to everyone) -------------------------
    if _matches_any(norm, GLOBAL_DENY_PATTERNS):
        _block(
            "guard_write: '{}' is in a globally protected path".format(file_path)
        )

    # ----- Agent-only deny check -------------------------------------------
    if agent_role and _matches_any(norm, AGENT_DENY_PATTERNS):
        _block(
            "guard_write: agents may not write '{}' (agent-restricted path)".format(file_path)
        )

    # Main session (no role) is trusted; past global deny it may write anywhere.
    if not agent_role:
        _allow()

    # ----- Agent allow check -----------------------------------------------
    if not _matches_any(norm, ALLOW_PATTERNS):
        _block(
            "guard_write: '{}' is not in the agent allow list; write rejected".format(file_path)
        )

    # ----- Role-based check ------------------------------------------------
    if agent_role:
        role_pattern = ROLE_PATTERNS.get(agent_role)
        if role_pattern is None:
            _block(
                "guard_write: unknown CLAUDE_AGENT_ROLE '{}'; write denied by default".format(agent_role)
            )
        if not _match(norm, role_pattern):
            _block(
                "guard_write: role '{}' may only write to '{}'; '{}' is outside that scope".format(
                    agent_role, role_pattern, file_path
                )
            )

    _allow()


if __name__ == "__main__":
    main()
