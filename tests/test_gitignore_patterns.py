#!/usr/bin/env python3
"""
Comprehensive test suite for gitignore-compatible pattern matching.
Tests all GitHub .gitignore pattern features that should be supported.
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


class TestGitignorePatternCompatibility:
    """Test complete gitignore pattern compatibility."""

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
            f"Tool: {tool_name}, Input: {tool_input}\n"
            f"stderr: {result.stderr[:400]}"
        )

        return result

    # ============================================================================
    # GLOBSTAR PATTERNS (**)
    # ============================================================================

    def test_globstar_match_anywhere(self):
        """** should match files at any depth in directory tree."""
        self.create_sensitive_file([
            "**/secrets.json"
        ])

        # Should match at root
        self.run_hook("Read", {"file_path": "secrets.json"}, 2)

        # Should match at any depth
        self.run_hook("Read", {"file_path": "config/secrets.json"}, 2)
        self.run_hook("Read", {"file_path": "app/config/secrets.json"}, 2)
        self.run_hook("Read", {"file_path": "deep/nested/path/secrets.json"}, 2)

        # Should NOT match different filename
        self.run_hook("Read", {"file_path": "secrets.txt"}, 0)
        self.run_hook("Read", {"file_path": "config/other.json"}, 0)

    def test_globstar_in_middle_of_pattern(self):
        """** in middle of pattern should match zero or more directories."""
        self.create_sensitive_file([
            "config/**/production.yaml"
        ])

        # Should match directly under config
        self.run_hook("Read", {"file_path": "config/production.yaml"}, 2)

        # Should match nested under config
        self.run_hook("Read", {"file_path": "config/app/production.yaml"}, 2)
        self.run_hook("Read", {"file_path": "config/env/prod/production.yaml"}, 2)

        # Should NOT match outside config directory
        self.run_hook("Read", {"file_path": "production.yaml"}, 0)
        self.run_hook("Read", {"file_path": "other/production.yaml"}, 0)

    def test_globstar_at_end_of_pattern(self):
        """Pattern ending with /** should match all files in directory tree."""
        self.create_sensitive_file([
            "secrets/**"
        ])

        # Should match everything under secrets/
        self.run_hook("Read", {"file_path": "secrets/api-keys.txt"}, 2)
        self.run_hook("Read", {"file_path": "secrets/db/passwords.txt"}, 2)
        self.run_hook("Read", {"file_path": "secrets/deep/nested/file.txt"}, 2)

        # Should NOT match the directory name elsewhere
        self.run_hook("Read", {"file_path": "src/secrets/component.js"}, 0)
        self.run_hook("Read", {"file_path": "other.txt"}, 0)

    def test_multiple_globstars(self):
        """Multiple ** in pattern should work correctly."""
        self.create_sensitive_file([
            "**/config/**/prod.*"
        ])

        # Should match with various depths
        self.run_hook("Read", {"file_path": "config/prod.yaml"}, 2)
        self.run_hook("Read", {"file_path": "app/config/prod.json"}, 2)
        self.run_hook("Read", {"file_path": "src/app/config/env/prod.yaml"}, 2)

        # Should NOT match without config in path
        self.run_hook("Read", {"file_path": "prod.yaml"}, 0)
        self.run_hook("Read", {"file_path": "app/prod.yaml"}, 0)

    # ============================================================================
    # NEGATION PATTERNS (!)
    # ============================================================================

    def test_negation_basic(self):
        """Negation with ! should exclude files from previous patterns."""
        self.create_sensitive_file([
            "*.log",
            "!important.log"
        ])

        # Should block most log files
        self.run_hook("Read", {"file_path": "debug.log"}, 2)
        self.run_hook("Read", {"file_path": "error.log"}, 2)

        # Should allow the negated file
        self.run_hook("Read", {"file_path": "important.log"}, 0)

    def test_negation_with_path(self):
        """Negation should work with path patterns."""
        self.create_sensitive_file([
            "*.env",
            "!test.env"
        ])

        # Should block most .env files
        self.run_hook("Read", {"file_path": ".env"}, 2)
        self.run_hook("Read", {"file_path": "production.env"}, 2)
        self.run_hook("Read", {"file_path": "config/.env"}, 2)

        # Should allow test.env anywhere
        self.run_hook("Read", {"file_path": "test.env"}, 0)
        self.run_hook("Read", {"file_path": "config/test.env"}, 0)

    def test_negation_with_globstar(self):
        """Negation should work with globstar patterns."""
        self.create_sensitive_file([
            "**/secrets/**",
            "!**/secrets/public/**"
        ])

        # Should block files in secrets directories
        self.run_hook("Read", {"file_path": "secrets/api-key.txt"}, 2)
        self.run_hook("Read", {"file_path": "app/secrets/private.txt"}, 2)

        # Should allow files in secrets/public
        self.run_hook("Read", {"file_path": "secrets/public/readme.txt"}, 0)
        self.run_hook("Read", {"file_path": "app/secrets/public/info.txt"}, 0)

    def test_negation_ordering(self):
        """Later patterns should override earlier ones (last match wins)."""
        self.create_sensitive_file([
            "*.txt",
            "!public.txt",
            "config/*.txt"  # Re-blocks txt files in config
        ])

        # Should allow public.txt at root
        self.run_hook("Read", {"file_path": "public.txt"}, 0)

        # Should block public.txt in config (later pattern)
        self.run_hook("Read", {"file_path": "config/public.txt"}, 2)

        # Should block other txt files in config
        self.run_hook("Read", {"file_path": "config/private.txt"}, 2)

    def test_multiple_negations(self):
        """Multiple negations should work correctly."""
        self.create_sensitive_file([
            "*.json",
            "!package.json",
            "!tsconfig.json",
            "!*.config.json"
        ])

        # Should block most JSON files
        self.run_hook("Read", {"file_path": "data.json"}, 2)
        self.run_hook("Read", {"file_path": "secrets.json"}, 2)

        # Should allow all negated patterns
        self.run_hook("Read", {"file_path": "package.json"}, 0)
        self.run_hook("Read", {"file_path": "tsconfig.json"}, 0)
        self.run_hook("Read", {"file_path": "webpack.config.json"}, 0)

    # ============================================================================
    # ROOT-RELATIVE PATTERNS (leading /)
    # ============================================================================

    def test_root_relative_pattern(self):
        """Leading / should match only from repository root."""
        self.create_sensitive_file([
            "/secrets.json"
        ])

        # Should match at root only
        self.run_hook("Read", {"file_path": "secrets.json"}, 2)
        self.run_hook("Read", {"file_path": "/secrets.json"}, 2)

        # Should NOT match in subdirectories
        self.run_hook("Read", {"file_path": "config/secrets.json"}, 0)
        self.run_hook("Read", {"file_path": "app/secrets.json"}, 0)

    def test_root_relative_directory_pattern(self):
        """Leading / with directory should match only from root."""
        self.create_sensitive_file([
            "/config/production.*"
        ])

        # Should match directly under root config
        self.run_hook("Read", {"file_path": "config/production.yaml"}, 2)
        self.run_hook("Read", {"file_path": "/config/production.json"}, 2)

        # Should NOT match nested config directories
        self.run_hook("Read", {"file_path": "app/config/production.yaml"}, 0)
        self.run_hook("Read", {"file_path": "src/config/production.json"}, 0)

    def test_no_leading_slash_matches_anywhere(self):
        """Patterns without leading / should match at any level."""
        self.create_sensitive_file([
            "secrets.json"
        ])

        # Should match at any level
        self.run_hook("Read", {"file_path": "secrets.json"}, 2)
        self.run_hook("Read", {"file_path": "config/secrets.json"}, 2)
        self.run_hook("Read", {"file_path": "app/config/secrets.json"}, 2)

    # ============================================================================
    # DIRECTORY-ONLY PATTERNS (trailing /)
    # ============================================================================

    def test_directory_only_pattern(self):
        """Trailing / should match directories only, not files."""
        self.create_sensitive_file([
            "build/",
            "dist/"
        ])

        # Should match files inside the directory
        self.run_hook("Read", {"file_path": "build/output.js"}, 2)
        self.run_hook("Read", {"file_path": "dist/bundle.js"}, 2)
        self.run_hook("Read", {"file_path": "build/nested/file.txt"}, 2)

        # Should NOT match files with same name (not directories)
        # Note: This is hard to test without filesystem, so we test the inverse:
        # A file named "build" (without slash) should not match "build/"
        # This might need implementation-specific testing

    # ============================================================================
    # ESCAPE SEQUENCES
    # ============================================================================

    def test_escape_hash(self):
        """\\# should match literal # character."""
        self.create_sensitive_file([
            "\\#important.txt"
        ])

        # Should match file starting with #
        self.run_hook("Read", {"file_path": "#important.txt"}, 2)

        # Should NOT match files without #
        self.run_hook("Read", {"file_path": "important.txt"}, 0)

    def test_escape_exclamation(self):
        """\\! should match literal ! character."""
        self.create_sensitive_file([
            "\\!readme.txt"
        ])

        # Should match file starting with !
        self.run_hook("Read", {"file_path": "!readme.txt"}, 2)

        # Should NOT treat as negation
        self.run_hook("Read", {"file_path": "readme.txt"}, 0)

    def test_escape_asterisk(self):
        """\\* should match literal * character."""
        self.create_sensitive_file([
            "file\\*.txt"
        ])

        # Should match file with literal *
        self.run_hook("Read", {"file_path": "file*.txt"}, 2)

        # Should NOT match as wildcard
        self.run_hook("Read", {"file_path": "file123.txt"}, 0)
        self.run_hook("Read", {"file_path": "fileabc.txt"}, 0)

    def test_escape_backslash(self):
        """Escaped backslash should match literal backslash."""
        self.create_sensitive_file([
            "path\\\\with\\\\backslash.txt"
        ])

        # Should match path with literal backslashes (Windows-style)
        # Note: This depends on platform handling

    # ============================================================================
    # WHITESPACE HANDLING
    # ============================================================================

    def test_trailing_whitespace_ignored(self):
        """Trailing whitespace should be trimmed from patterns."""
        self.create_sensitive_file([
            "*.env   ",  # Trailing spaces
            "secrets.json\t",  # Trailing tab
        ])

        # Should match despite trailing whitespace in pattern
        self.run_hook("Read", {"file_path": ".env"}, 2)
        self.run_hook("Read", {"file_path": "secrets.json"}, 2)

    def test_leading_whitespace_ignored(self):
        """Leading whitespace should be trimmed from patterns."""
        self.create_sensitive_file([
            "   *.log",  # Leading spaces
            "\t*.tmp",  # Leading tab
        ])

        # Should match despite leading whitespace in pattern
        self.run_hook("Read", {"file_path": "debug.log"}, 2)
        self.run_hook("Read", {"file_path": "cache.tmp"}, 2)

    def test_escaped_trailing_space(self):
        """Escaped trailing space should be preserved."""
        self.create_sensitive_file([
            "file\\ with\\ space.txt"
        ])

        # Should match file with spaces
        self.run_hook("Read", {"file_path": "file with space.txt"}, 2)

    # ============================================================================
    # COMPLEX PATTERN COMBINATIONS
    # ============================================================================

    def test_complex_terraform_patterns(self):
        """Real-world Terraform sensitive patterns."""
        self.create_sensitive_file([
            "# Terraform sensitive files",
            "*.tfvars",
            "*.tfvars.json",
            "!example.tfvars",
            "**/environments/prod/**",
            "!**/environments/prod/README.md"
        ])

        # Should block tfvars files
        self.run_hook("Read", {"file_path": "terraform.tfvars"}, 2)
        self.run_hook("Read", {"file_path": "prod.auto.tfvars"}, 2)

        # Should allow example
        self.run_hook("Read", {"file_path": "example.tfvars"}, 0)

        # Should block prod environment
        self.run_hook("Read", {"file_path": "environments/prod/secrets.tf"}, 2)
        self.run_hook("Read", {"file_path": "app/environments/prod/config.tf"}, 2)

        # Should allow README in prod
        self.run_hook("Read", {"file_path": "environments/prod/README.md"}, 0)

    def test_complex_credentials_patterns(self):
        """Real-world credentials patterns."""
        self.create_sensitive_file([
            "**/*.key",
            "**/*.pem",
            "**/credentials/**",
            "!**/credentials/README.md",
            ".env*",
            "!.env.example",
            "/config/production.*",
        ])

        # Should block key/pem files anywhere
        self.run_hook("Read", {"file_path": "app/certs/server.key"}, 2)
        self.run_hook("Read", {"file_path": "ssl/cert.pem"}, 2)

        # Should block credentials directory
        self.run_hook("Read", {"file_path": "aws/credentials/access.json"}, 2)

        # Should allow README
        self.run_hook("Read", {"file_path": "aws/credentials/README.md"}, 0)

        # Should block .env files
        self.run_hook("Read", {"file_path": ".env"}, 2)
        self.run_hook("Read", {"file_path": ".env.local"}, 2)

        # Should allow example
        self.run_hook("Read", {"file_path": ".env.example"}, 0)

        # Should block root production config only
        self.run_hook("Read", {"file_path": "config/production.yaml"}, 2)
        self.run_hook("Read", {"file_path": "app/config/production.yaml"}, 0)

    def test_case_sensitivity_with_gitignore_patterns(self):
        """Pattern matching should be case-insensitive (like current implementation)."""
        self.create_sensitive_file([
            "*.ENV",
            "**/Secrets/**"
        ])

        # Should match case-insensitively
        self.run_hook("Read", {"file_path": ".env"}, 2)
        self.run_hook("Read", {"file_path": "production.ENV"}, 2)
        self.run_hook("Read", {"file_path": "app/secrets/key.txt"}, 2)
        self.run_hook("Read", {"file_path": "app/SECRETS/key.txt"}, 2)

    def test_pattern_with_question_mark(self):
        """? wildcard should match single character."""
        self.create_sensitive_file([
            "secret?.json",
            "file-?.txt"
        ])

        # Should match single character
        self.run_hook("Read", {"file_path": "secret1.json"}, 2)
        self.run_hook("Read", {"file_path": "secreta.json"}, 2)
        self.run_hook("Read", {"file_path": "file-x.txt"}, 2)

        # Should NOT match multiple characters
        self.run_hook("Read", {"file_path": "secret12.json"}, 0)
        self.run_hook("Read", {"file_path": "secret.json"}, 0)

    def test_pattern_with_brackets(self):
        """[...] should match character ranges."""
        self.create_sensitive_file([
            "secret[0-9].json",
            "file[abc].txt"
        ])

        # Should match characters in range
        self.run_hook("Read", {"file_path": "secret5.json"}, 2)
        self.run_hook("Read", {"file_path": "filea.txt"}, 2)
        self.run_hook("Read", {"file_path": "fileb.txt"}, 2)

        # Should NOT match outside range
        self.run_hook("Read", {"file_path": "secretx.json"}, 0)
        self.run_hook("Read", {"file_path": "filex.txt"}, 0)

    # ============================================================================
    # BASH COMMAND INTEGRATION
    # ============================================================================

    def test_bash_commands_with_globstar_patterns(self):
        """Bash commands should respect globstar patterns."""
        self.create_sensitive_file([
            "**/secrets.json"
        ])

        # Should block access to secrets at any depth
        self.run_hook("Bash", {"command": "cat config/secrets.json"}, 2)
        self.run_hook("Bash", {"command": "vim app/config/secrets.json"}, 2)

        # Should allow other files
        self.run_hook("Bash", {"command": "cat config/settings.json"}, 0)

    def test_bash_commands_with_negation_patterns(self):
        """Bash commands should respect negation patterns."""
        self.create_sensitive_file([
            "*.log",
            "!access.log"
        ])

        # Should block most log files
        self.run_hook("Bash", {"command": "cat error.log"}, 2)

        # Should allow negated file
        self.run_hook("Bash", {"command": "cat access.log"}, 0)
