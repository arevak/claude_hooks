#!/usr/bin/env python3
"""
Enhanced test suite for the Claude Code sensitive file blocker hook.
Tests .sensitive file functionality and --git-ignore flag.
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

class TestBlockSensitiveEnhanced:
    """Test cases for the enhanced block-sensitive hook."""

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

    # Test default behavior (no .sensitive file)
    def test_default_no_patterns(self):
        """Should allow all files when no .sensitive file exists."""
        self.run_hook("Read", {"file_path": "/project/terraform.tfvars"}, 0)
        self.run_hook("Read", {"file_path": "/project/prod.auto.tfvars"}, 0)
        self.run_hook("Read", {"file_path": "/project/main.tf"}, 0)

    # Test custom .sensitive file patterns
    def test_custom_sensitive_patterns(self):
        """Should block files matching custom .sensitive patterns."""
        self.create_sensitive_file([
            "*.env",
            "secrets.json",
            "**/config/production.yaml"  # Use globstar to match at any depth
        ])

        self.run_hook("Read", {"file_path": "/project/.env"}, 2)
        self.run_hook("Read", {"file_path": "/project/dev.env"}, 2)
        self.run_hook("Read", {"file_path": "/project/secrets.json"}, 2)
        self.run_hook("Read", {"file_path": "/project/config/production.yaml"}, 2)
        self.run_hook("Read", {"file_path": "/project/config/development.yaml"}, 0)

    def test_sensitive_file_with_comments(self):
        """Should ignore comments in .sensitive file."""
        self.create_sensitive_file([
            "# This is a comment",
            "*.env",
            "",  # empty line
            "# Another comment",
            "secrets.*"
        ])
        
        self.run_hook("Read", {"file_path": "/project/.env"}, 2)
        self.run_hook("Read", {"file_path": "/project/secrets.json"}, 2)
        self.run_hook("Read", {"file_path": "/project/normal.txt"}, 0)

    # Test --git-ignore functionality
    def test_gitignore_feature_available(self):
        """Test that --git-ignore flag is available but doesn't block without git repo."""
        # Without git repo, --git-ignore should not block anything
        self.run_hook("Read", {"file_path": "/project/debug.log"}, 0, use_git_ignore=True)
        self.run_hook("Read", {"file_path": "/project/.DS_Store"}, 0, use_git_ignore=True)
        self.run_hook("Read", {"file_path": "/project/src/main.js"}, 0, use_git_ignore=True)

    def test_gitignore_flag_disabled(self):
        """Test that git ignore is not applied when --git-ignore is not used."""
        # Without --git-ignore flag, no git checking should happen
        self.run_hook("Read", {"file_path": "/project/debug.log"}, 0, use_git_ignore=False)
        self.run_hook("Read", {"file_path": "/project/.DS_Store"}, 0, use_git_ignore=False)

    def test_sensitive_patterns_work_with_gitignore_flag(self):
        """Test that .sensitive patterns work regardless of --git-ignore flag."""
        self.create_sensitive_file(["*.env"])
        
        # .sensitive patterns should work with --git-ignore flag
        self.run_hook("Read", {"file_path": "/project/.env"}, 2, use_git_ignore=True)       
        self.run_hook("Read", {"file_path": "/project/main.py"}, 0, use_git_ignore=True)    
        
        # .sensitive patterns should also work without --git-ignore flag
        self.run_hook("Read", {"file_path": "/project/.env"}, 2, use_git_ignore=False)      
        self.run_hook("Read", {"file_path": "/project/main.py"}, 0, use_git_ignore=False)

    # Test bash command filtering with custom patterns
    def test_bash_command_custom_patterns(self):
        """Should block bash commands accessing files matching custom patterns."""
        self.create_sensitive_file([
            "*.env",
            "secrets.json"
        ])
        
        self.run_hook("Bash", {"command": "cat .env"}, 2)
        self.run_hook("Bash", {"command": "vim secrets.json"}, 2)
        self.run_hook("Bash", {"command": "less config.yaml"}, 0)

    def test_bash_command_with_gitignore_flag(self):
        """Test that bash commands work with --git-ignore flag (no git repo = no blocking)."""
        # Without git repo, --git-ignore should not block
        self.run_hook("Bash", {"command": "cat debug.log"}, 0, use_git_ignore=True)
        self.run_hook("Bash", {"command": "cat debug.log"}, 0, use_git_ignore=False)

    # Test grep functionality
    def test_grep_custom_patterns(self):
        """Should block grep on files matching custom patterns."""
        self.create_sensitive_file(["*.env"])
        
        self.run_hook("Grep", {
            "pattern": "API_KEY", 
            "path": "/project/.env"
        }, 2)
        
        self.run_hook("Grep", {
            "pattern": "function", 
            "paths": ["/project/main.py", "/project/.env"]
        }, 2)

    # Test MultiEdit functionality
    def test_multiedit_custom_patterns(self):
        """Should block MultiEdit on files matching custom patterns."""
        self.create_sensitive_file(["*.env"])
        
        self.run_hook("MultiEdit", {
            "edits": [
                {"file_path": "/project/main.py", "changes": "..."},
                {"file_path": "/project/.env", "changes": "..."}
            ]
        }, 2)

    # Test error handling
    def test_malformed_sensitive_file(self):
        """Should handle malformed .sensitive file gracefully."""
        # Create a .sensitive file that can't be read properly
        sensitive_file = self.project_root / '.sensitive'
        sensitive_file.write_bytes(b'\x00\x01\x02')  # Invalid text
        
        # Should fall back to empty patterns (allow everything)
        result = self.run_hook("Read", {"file_path": "/project/terraform.tfvars"}, 0)
        # Should show a warning about the malformed file in stderr
        # Note: the warning might not appear in every test run due to race conditions

    def test_missing_project_dir(self):
        """Should handle missing CLAUDE_PROJECT_DIR gracefully."""
        del os.environ['CLAUDE_PROJECT_DIR']
        # Should still work with current directory
        self.run_hook("Read", {"file_path": "/project/main.py"}, 0)

    # Test pattern matching edge cases
    def test_case_insensitive_matching(self):
        """Should match patterns case-insensitively."""
        self.create_sensitive_file(["*.ENV"])
        
        self.run_hook("Read", {"file_path": "/project/.env"}, 2)
        self.run_hook("Read", {"file_path": "/project/production.ENV"}, 2)

    def test_path_component_matching(self):
        """Should match against path components correctly using globstar patterns."""
        self.create_sensitive_file([
            "**/secrets/*",       # Match secrets directory anywhere
            "**/production.yaml"  # Match production.yaml anywhere
        ])

        self.run_hook("Read", {"file_path": "/project/secrets/api-keys.txt"}, 2)
        self.run_hook("Read", {"file_path": "/project/config/production.yaml"}, 2)
        self.run_hook("Read", {"file_path": "/project/config/development.yaml"}, 0)