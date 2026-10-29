"""
Tests for .claude/hooks/guard_write.py

Runs the hook as a subprocess, passes JSON via stdin, and asserts on:
  - exit code (0 = allow, 2 = block)
  - the "decision" field in stdout JSON
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HOOK = REPO_ROOT / ".claude" / "hooks" / "guard_write.py"


def _run(tool_name, file_path=None, role=None):
    """Invoke the hook and return (exit_code, parsed_stdout_json)."""
    tool_input = {}
    if file_path is not None:
        tool_input["file_path"] = file_path

    payload = {"tool_name": tool_name, "tool_input": tool_input}

    env = os.environ.copy()
    if role is not None:
        env["CLAUDE_AGENT_ROLE"] = role
    else:
        env.pop("CLAUDE_AGENT_ROLE", None)

    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        output = {"decision": "__parse_error__", "raw": result.stdout}

    return result.returncode, output


# --------------------------------------------------------------------------- #
# Tests (per V5-WP4 spec)
# --------------------------------------------------------------------------- #


class TestMainSessionBlocked:
    """Main session (no CLAUDE_AGENT_ROLE) still can't write truly sensitive paths."""

    def test_block_docx(self):
        """主会话写 docs/x.docx → block（PRD docx 不得被模型覆盖）"""
        code, out = _run("Write", "docs/x.docx")
        assert code == 2
        assert out["decision"] == "block"


class TestMainSessionAllowed:
    """Main session (no CLAUDE_AGENT_ROLE) owns integration — may write src/data/schemas."""

    def test_allow_projects_any_path(self):
        code, out = _run("Write", "projects/37-jiaren/anything.md")
        assert code == 0
        assert out["decision"] == "allow"

    def test_allow_src_file(self):
        """主会话写 src/gxwd/composer.py → allow（主会话负责集成）"""
        code, out = _run("Write", "src/gxwd/composer.py")
        assert code == 0
        assert out["decision"] == "allow"

    def test_allow_data_hexagrams(self):
        code, out = _run("Write", "data/hexagrams.json")
        assert code == 0
        assert out["decision"] == "allow"


class TestAgentBlockedOnSrc:
    """Agent with role must not write src/, data/, schemas/."""

    def test_block_src_from_agent(self):
        code, out = _run("Write", "src/gxwd/foo.py", role="classics-researcher")
        assert code == 2
        assert out["decision"] == "block"

    def test_block_data_from_agent(self):
        code, out = _run("Write", "data/hexagrams.json", role="ink-art-director")
        assert code == 2
        assert out["decision"] == "block"

    def test_block_pyproject_from_agent(self):
        """pyproject.toml 对 Agent 禁写（打包配置是集成责任）"""
        code, out = _run("Write", "pyproject.toml", role="classics-researcher")
        assert code == 2
        assert out["decision"] == "block"


class TestClassicsResearcher:
    """classics-researcher may only write to projects/*/research/**."""

    def test_allow_research_path(self):
        """CLAUDE_AGENT_ROLE=classics-researcher 写 projects/37-jiaren/research/x.md → allow"""
        code, out = _run("Write", "projects/37-jiaren/research/x.md", role="classics-researcher")
        assert code == 0
        assert out["decision"] == "allow"

    def test_block_art_path(self):
        """CLAUDE_AGENT_ROLE=classics-researcher 写 projects/37-jiaren/art/x.md → block"""
        code, out = _run("Write", "projects/37-jiaren/art/x.md", role="classics-researcher")
        assert code == 2
        assert out["decision"] == "block"


class TestInkArtDirector:
    """ink-art-director may only write to projects/*/art/**."""

    def test_allow_art_path(self):
        """CLAUDE_AGENT_ROLE=ink-art-director 写 projects/37-jiaren/art/x.md → allow"""
        code, out = _run("Write", "projects/37-jiaren/art/x.md", role="ink-art-director")
        assert code == 0
        assert out["decision"] == "allow"


class TestIndependentVerifier:
    """independent-verifier may only write to projects/*/reviews/**."""

    def test_allow_reviews_path(self):
        """CLAUDE_AGENT_ROLE=independent-verifier 写 projects/37-jiaren/reviews/g1-x.json → allow"""
        code, out = _run("Write", "projects/37-jiaren/reviews/g1-x.json", role="independent-verifier")
        assert code == 0
        assert out["decision"] == "allow"

    def test_block_research_path(self):
        """CLAUDE_AGENT_ROLE=independent-verifier 写 projects/37-jiaren/research/x.md → block"""
        code, out = _run("Write", "projects/37-jiaren/research/x.md", role="independent-verifier")
        assert code == 2
        assert out["decision"] == "block"


class TestNonWriteTools:
    """Non-Write/Edit tools must always be allowed."""

    def test_allow_bash(self):
        """tool_name=Bash 时 → allow（本 hook 只管写入）"""
        code, out = _run("Bash", "data/hexagrams.json")
        assert code == 0
        assert out["decision"] == "allow"

    def test_allow_bash_no_path(self):
        """tool_name=Bash 无 file_path → allow"""
        code, out = _run("Bash")
        assert code == 0
        assert out["decision"] == "allow"


class TestMalformedInput:
    """Missing file_path on Write/Edit is a hard block."""

    def test_block_write_without_file_path(self):
        """tool_name=Write 但没有 file_path → block（输入异常）"""
        code, out = _run("Write", file_path=None)
        assert code == 2
        assert out["decision"] == "block"
