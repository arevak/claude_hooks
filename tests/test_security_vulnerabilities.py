#!/usr/bin/env python3
"""
Proof-of-concept tests demonstrating security vulnerabilities in block_sensitive hook.
These tests show how the current implementation can be bypassed.
"""

import pytest
import json
from claude_hooks.block_sensitive import process_tool_input, load_sensitive_patterns, find_project_root


class TestGrepVulnerabilities:
    """Test vulnerabilities in Grep tool handling."""

    def test_grep_without_path_bypasses_check(self, tmp_path):
        """
        VULNERABILITY: Grep without path parameter bypasses sensitive file check.
        The hook only checks if 'path' key exists in tool_input, but Grep can
        operate on current directory without specifying a path.
        """
        # Setup: Create .sensitive file
        sensitive_file = tmp_path / '.sensitive'
        sensitive_file.write_text('*.env\n.tfvars\nsecrets/')

        # Create PathSpec
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env', '.tfvars', 'secrets/'])

        # Test: Grep with no path parameter
        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Grep',
            'tool_input': {
                'pattern': 'API_KEY',
                # No 'path' parameter - searches current directory
                'type': 'py'  # Could be any file type
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        # VULNERABILITY: This should block but doesn't!
        assert should_block is False, "Grep without path bypasses security check!"
        print("❌ VULNERABILITY CONFIRMED: Grep without path parameter is allowed")

    def test_grep_with_recursive_flag_bypasses(self, tmp_path):
        """
        VULNERABILITY: Grep with recursive search but no path bypasses check.
        """
        sensitive_file = tmp_path / '.sensitive'
        sensitive_file.write_text('*.env\nsecrets/')

        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env', 'secrets/'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Grep',
            'tool_input': {
                'pattern': 'password',
                'output_mode': 'content',
                # Recursive search with no path - searches everything
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        assert should_block is False
        print("❌ VULNERABILITY CONFIRMED: Recursive Grep without path is allowed")


class TestBashFindGrepVulnerabilities:
    """Test vulnerabilities in Bash command checking with find+grep combinations."""

    def test_find_piped_to_xargs_cat_bypasses(self, tmp_path):
        """
        VULNERABILITY: Piped commands bypass token-based checking.
        find . -name "*.tfvars" | xargs cat
        """
        sensitive_file = tmp_path / '.sensitive'
        sensitive_file.write_text('*.tfvars\n*.env')

        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.tfvars', '*.env'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'find . -name "*.tfvars" | xargs cat'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        # VULNERABILITY: Pipe to xargs makes filenames invisible
        # Note: The legacy patterns might catch this specific case, but let's see
        print(f"Result: block={should_block}, message={message}")
        if not should_block:
            print("❌ VULNERABILITY: find | xargs cat bypasses detection")

    def test_find_with_exec_bypasses(self, tmp_path):
        """
        VULNERABILITY: find -exec uses {} placeholder invisible to hook.
        find . -name "*.tfvars" -exec cat {} \\;
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.tfvars'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'find . -name "*.tfvars" -exec cat {} \\;'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        print(f"Result: block={should_block}, message={message}")
        if not should_block:
            print("❌ VULNERABILITY: find -exec bypasses detection")

    def test_command_substitution_bypasses(self, tmp_path):
        """
        VULNERABILITY: Command substitution evaluated at runtime.
        cat $(find . -name ".env")
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env', '.env'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'cat $(find . -name ".env")'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        print(f"Result: block={should_block}, message={message}")
        if not should_block:
            print("❌ VULNERABILITY: command substitution bypasses detection")

    def test_process_substitution_bypasses(self, tmp_path):
        """
        VULNERABILITY: Process substitution creates temp fd.
        grep "password" <(find . -name "*.env")
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'grep "password" <(find . -name "*.env")'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        print(f"Result: block={should_block}, message={message}")
        if not should_block:
            print("❌ VULNERABILITY: process substitution bypasses detection")

    def test_wildcard_expansion_bypasses(self, tmp_path):
        """
        VULNERABILITY: Wildcards expanded by shell after command sent.
        cat *.tfvars
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.tfvars'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'cat *.tfvars'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        print(f"Result: block={should_block}, message={message}")
        # This one might be caught by legacy patterns

    def test_flag_with_equals_bypasses(self, tmp_path):
        """
        VULNERABILITY: Flags with = are skipped entirely.
        somecommand --file=secret.tfvars
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.tfvars'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'terraform plan --var-file=custom.tfvars --out=plan.out'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        print(f"Result: block={should_block}, message={message}")
        # Note: This is actually legitimate terraform usage, so it's a balance


class TestRipgrepVulnerabilities:
    """Test vulnerabilities in ripgrep (rg) command handling."""

    def test_ripgrep_without_path_bypasses(self, tmp_path):
        """
        VULNERABILITY: Ripgrep without path parameter searches recursively.
        rg "password" --type yaml
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env', 'secrets/'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'rg "password" --type yaml'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        assert should_block is False
        print("❌ VULNERABILITY CONFIRMED: ripgrep without path bypasses detection")

    def test_ripgrep_with_type_filter_bypasses(self, tmp_path):
        """
        VULNERABILITY: Ripgrep with type filters searches all matching files.
        rg "API_KEY" --type env
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'rg "API_KEY" --type-add "custom:*.env" --type custom'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        print(f"Result: block={should_block}, message={message}")
        if not should_block:
            print("❌ VULNERABILITY: ripgrep with custom type bypasses detection")


class TestAwkVulnerabilities:
    """Test vulnerabilities in AWK command handling."""

    def test_awk_variable_indirection_bypasses(self, tmp_path):
        """
        VULNERABILITY: AWK -v variable assignment bypasses detection.
        awk -v file=.env '{getline < file; print}' /dev/null
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'awk -v file=.env \'{getline < file; print}\' /dev/null'
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        assert should_block is False
        print("❌ VULNERABILITY CONFIRMED: AWK variable indirection bypasses detection")

    def test_awk_getline_inline_bypasses(self, tmp_path):
        """
        VULNERABILITY: AWK getline with inline filename bypasses detection.
        awk 'BEGIN {while(getline < ".env") print}'
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'awk \'BEGIN {while(getline < ".env") print}\''
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        assert should_block is False
        print("❌ VULNERABILITY CONFIRMED: AWK inline getline bypasses detection")

    def test_awk_system_command_injection_bypasses(self, tmp_path):
        """
        VULNERABILITY: AWK system() executes arbitrary commands.
        awk 'BEGIN {system("cat .env")}'
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.env'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'awk \'BEGIN {system("cat .env")}\''
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        assert should_block is False
        print("❌ VULNERABILITY CONFIRMED: AWK system() command injection bypasses detection")

    def test_awk_nested_find_bypasses(self, tmp_path):
        """
        VULNERABILITY: AWK system() with nested find command.
        awk 'BEGIN {system("find . -name *.tfvars | xargs cat")}'
        """
        import pathspec
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ['*.tfvars'])

        data = {
            'hook_event_name': 'PreToolUse',
            'tool_name': 'Bash',
            'tool_input': {
                'command': 'awk \'BEGIN {system("find . -name *.tfvars | xargs cat")}\''
            }
        }

        should_block, message = process_tool_input(data, spec, tmp_path, use_gitignore=False)

        print(f"Result: block={should_block}, message={message}")
        if not should_block:
            print("❌ VULNERABILITY: AWK with nested find command bypasses detection")


class TestRecommendedFixes:
    """
    Recommended fixes for these vulnerabilities:

    1. GREP/RIPGREP TOOL:
       - Check if 'path' is empty/missing and default to '.'
       - Block Grep/Ripgrep operations when path would expose sensitive directories
       - Consider blocking recursive grep/rg without explicit safe paths
       - Validate ripgrep --type and --glob flags against sensitive patterns

    2. BASH COMMAND:
       - Detect pipe operators and flag risky combinations (find | xargs)
       - Parse find commands and extract -name/-path patterns
       - Detect -exec flag and analyze the command template
       - Block command substitution $() and process substitution <()
       - Parse --flag=value syntax to extract values
       - Use AST parsing instead of simple tokenization

    3. AWK SECURITY:
       - Detect and block 'getline' in AWK scripts (file access)
       - Detect and block 'system(' in AWK scripts (command execution)
       - Parse -v variable assignments and check values
       - Consider blocking AWK entirely in strict mode (too dangerous)
       - AWK variants: awk, gawk, mawk, nawk all need checking

    4. RIPGREP SECURITY:
       - Block ripgrep without explicit safe paths
       - Parse --type-add definitions and check patterns
       - Validate --glob patterns against sensitive files
       - Handle ripgrep's default recursive behavior

    5. GENERAL:
       - Add explicit allowlist mode for highly sensitive environments
       - Log all attempted accesses for audit trail
       - Consider blocking certain command combinations entirely
       - Add pattern detection for find commands specifically
       - Implement defense-in-depth with multiple validation layers
    """
    pass


if __name__ == '__main__':
    # Run tests manually to see vulnerabilities
    print("=" * 80)
    print("SECURITY VULNERABILITY PROOF-OF-CONCEPT TESTS")
    print("=" * 80)
    print()

    pytest.main([__file__, '-v', '-s'])
