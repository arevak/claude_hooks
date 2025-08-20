#!/usr/bin/env python3
"""
Basic compatibility test suite for the Claude Code sensitive file blocker hook.
For comprehensive tests, see test_block_sensitive_enhanced.py
"""

import pytest
import subprocess
import json
import sys
import tempfile
import os
from pathlib import Path

# Hook script path relative to project root
HOOK_SCRIPT = "src/claude_hooks/block_sensitive.py"

class TestBlockSensitiveHook:
    """Basic test cases for the block-sensitive hook."""

    def setup_method(self):
        """Set up test environment with temporary project directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        os.environ['CLAUDE_PROJECT_DIR'] = str(self.project_root)

    def teardown_method(self):
        """Clean up test environment."""
        if 'CLAUDE_PROJECT_DIR' in os.environ:
            del os.environ['CLAUDE_PROJECT_DIR']
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_sensitive_file(self, patterns):
        """Create a .sensitive file with given patterns."""
        sensitive_file = self.project_root / '.sensitive'
        with open(sensitive_file, 'w') as f:
            for pattern in patterns:
                f.write(f"{pattern}\n")

    def run_hook(self, tool_name, tool_input, expected_exit):
        """Run the hook script with given inputs and verify exit code."""
        test_data = {
            "session_id": "test-123",
            "transcript_path": "/Users/test/.claude/projects/test/session.jsonl",
            "cwd": str(self.project_root),
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input
        }
        
        # Run the hook script
        result = subprocess.run(
            [sys.executable, HOOK_SCRIPT],
            input=json.dumps(test_data),
            capture_output=True,
            text=True
        )
        
        assert result.returncode == expected_exit, (
            f"Expected exit code {expected_exit}, got {result.returncode}. "
            f"stderr: {result.stderr[:200]}"
        )
        
        return result

    # Test default behavior (no .sensitive file) - should allow everything
    def test_allow_all_when_no_sensitive_file(self):
        """Should allow all files when no .sensitive file exists"""
        self.run_hook("Read", {"file_path": "/project/terraform.tfvars"}, 0)
        self.run_hook("Read", {"file_path": "/project/secrets.json"}, 0)
        self.run_hook("Read", {"file_path": "/project/.env"}, 0)

    # Test with .sensitive file configured
    def test_block_with_sensitive_file(self):
        """Should block files matching patterns in .sensitive file"""
        self.create_sensitive_file([
            "terraform.tfvars",
            "*.env"
        ])
        
        self.run_hook("Read", {"file_path": "/project/terraform.tfvars"}, 2)
        self.run_hook("Read", {"file_path": "/project/.env"}, 2)
        self.run_hook("Read", {"file_path": "/project/main.tf"}, 0)

    def test_bash_command_blocking(self):
        """Should block bash commands accessing sensitive files"""
        self.create_sensitive_file(["*.env"])
        
        self.run_hook("Bash", {"command": "cat .env"}, 2)
        self.run_hook("Bash", {"command": "ls -la"}, 0)