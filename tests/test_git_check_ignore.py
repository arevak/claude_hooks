#!/usr/bin/env python3
"""
Test suite for git check-ignore integration using the wrapper function mock.
"""

import pytest
import subprocess
import json
import sys
import tempfile
import os
import unittest.mock as mock
from pathlib import Path

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from claude_hooks.block_sensitive import run_git_check_ignore, is_git_ignored

# Hook script path relative to project root
HOOK_SCRIPT = "src/claude_hooks/block_sensitive.py"


class TestGitCheckIgnoreFunctions:
    """Unit tests for git check-ignore functions."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_mock_git_result(self, returncode, stdout="", stderr=""):
        """Create a mock subprocess.CompletedProcess result."""
        result = mock.Mock()
        result.returncode = returncode
        result.stdout = stdout
        result.stderr = stderr
        return result

    @mock.patch('claude_hooks.block_sensitive.run_git_check_ignore')
    def test_is_git_ignored_file_ignored(self, mock_run_git):
        """Test is_git_ignored when file is ignored."""
        mock_run_git.return_value = self.create_mock_git_result(0, ".gitignore:1:*.log\tdebug.log\n")
        
        result = is_git_ignored("/project/debug.log", self.project_root)
        
        assert result == True
        mock_run_git.assert_called_once_with("/project/debug.log", self.project_root)

    @mock.patch('claude_hooks.block_sensitive.run_git_check_ignore')
    def test_is_git_ignored_file_not_ignored(self, mock_run_git):
        """Test is_git_ignored when file is not ignored."""
        mock_run_git.return_value = self.create_mock_git_result(1)
        
        result = is_git_ignored("/project/main.py", self.project_root)
        
        assert result == False
        mock_run_git.assert_called_once_with("/project/main.py", self.project_root)

    @mock.patch('claude_hooks.block_sensitive.run_git_check_ignore')
    def test_is_git_ignored_not_in_repo(self, mock_run_git):
        """Test is_git_ignored when not in git repository."""
        mock_run_git.return_value = self.create_mock_git_result(128, "", "fatal: not a git repository")
        
        result = is_git_ignored("/project/debug.log", self.project_root)
        
        assert result == False  # Should not block when not in repo

    @mock.patch('claude_hooks.block_sensitive.run_git_check_ignore')
    def test_is_git_ignored_git_not_found(self, mock_run_git):
        """Test is_git_ignored when git command is not found."""
        mock_run_git.side_effect = FileNotFoundError("git command not found")
        
        result = is_git_ignored("/project/debug.log", self.project_root)
        
        assert result == False  # Should not block when git not available

    @mock.patch('subprocess.run')
    def test_run_git_check_ignore_contract(self, mock_subprocess):
        """Test that run_git_check_ignore calls subprocess.run with correct arguments."""
        mock_subprocess.return_value = self.create_mock_git_result(0)
        
        result = run_git_check_ignore("/project/debug.log", self.project_root)
        
        mock_subprocess.assert_called_once_with(
            ['git', 'check-ignore', '/project/debug.log'],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

    def test_git_check_ignore_return_codes(self):
        """Test that we correctly interpret git check-ignore return codes."""
        test_cases = [
            (0, True),   # File is ignored
            (1, False),  # File is not ignored  
            (128, False), # Error (not in repo, etc.) - should not block
            (129, False), # Other error - should not block
        ]
        
        for returncode, expected_ignored in test_cases:
            with mock.patch('claude_hooks.block_sensitive.run_git_check_ignore') as mock_run_git:
                mock_run_git.return_value = self.create_mock_git_result(returncode)
                
                result = is_git_ignored("/project/test.log", self.project_root)
                assert result == expected_ignored, f"Return code {returncode} should result in {expected_ignored}"


class TestGitCheckIgnoreIntegration:
    """Basic integration tests for git check-ignore functionality."""

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

    def run_hook(self, tool_name, tool_input, expected_exit, use_git_ignore=False):
        """Run the hook script with given inputs and verify exit code."""
        test_data = {
            "session_id": "test-123",
            "transcript_path": "/Users/test/.claude/projects/test/session.jsonl",
            "cwd": str(self.project_root),
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input
        }
        
        # Build command with optional --git-ignore flag
        cmd = [sys.executable, HOOK_SCRIPT]
        if use_git_ignore:
            cmd.append('--git-ignore')
        
        # Run the hook script
        result = subprocess.run(
            cmd,
            input=json.dumps(test_data),
            capture_output=True,
            text=True
        )
        
        assert result.returncode == expected_exit, (
            f"Expected exit code {expected_exit}, got {result.returncode}. "
            f"stderr: {result.stderr[:400]}"
        )
        
        return result

    def test_git_ignore_flag_accepted(self):
        """Test that --git-ignore flag is accepted without errors."""
        # Without git repo, --git-ignore should not block anything (graceful fallback)
        self.run_hook("Read", {"file_path": "/project/debug.log"}, 0, use_git_ignore=True)
        self.run_hook("Read", {"file_path": "/project/main.py"}, 0, use_git_ignore=True)
        
    def test_git_ignore_flag_disabled(self):
        """Test that files are not blocked when --git-ignore is not used."""
        self.run_hook("Read", {"file_path": "/project/debug.log"}, 0, use_git_ignore=False)
        self.run_hook("Read", {"file_path": "/project/main.py"}, 0, use_git_ignore=False)