#!/usr/bin/env python3
"""
Claude Code hook to block direct access to sensitive files.
Supports .sensitive file patterns and optional .gitignore-style filtering.
"""

import sys
import json
import re
import os
import fnmatch
import argparse
import subprocess
from pathlib import Path

def find_project_root():
    """Find the project root directory from CLAUDE_PROJECT_DIR env var."""
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR')
    if project_dir and os.path.exists(project_dir):
        return Path(project_dir)
    return Path.cwd()

def load_sensitive_patterns(project_root):
    """Load sensitive file patterns from .sensitive file."""
    sensitive_file = project_root / '.sensitive'
    patterns = []
    
    # No default patterns - users must define their own in .sensitive file
    default_patterns = []
    
    if sensitive_file.exists():
        try:
            with open(sensitive_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read .sensitive file: {e}", file=sys.stderr)
            patterns = default_patterns
    else:
        patterns = default_patterns
    
    # If no patterns were loaded and we have no defaults, use defaults
    if not patterns:
        patterns = default_patterns
    
    return patterns

def run_git_check_ignore(filepath, project_root):
    """
    Run git check-ignore command and return the result.
    This wrapper allows for easy mocking in tests.
    
    Returns:
        subprocess.CompletedProcess: The result of the git check-ignore command
    """
    return subprocess.run(
        ['git', 'check-ignore', filepath],
        cwd=project_root,
        capture_output=True,
        text=True
    )

def is_git_ignored(filepath, project_root):
    """Check if a file is ignored by git using git check-ignore."""
    try:
        # Use git check-ignore to leverage git's own ignore logic
        result = run_git_check_ignore(filepath, project_root)
        # git check-ignore returns 0 if file is ignored, 1 if not ignored
        return result.returncode == 0
    except Exception:
        # If git is not available or any error occurs, don't block
        return False

def matches_pattern(filepath, patterns):
    """Check if filepath matches any of the given patterns."""
    if not filepath or not patterns:
        return False
    
    # Convert to Path for consistent handling
    path = Path(filepath)
    filename = path.name
    
    for pattern in patterns:
        pattern_lower = pattern.lower()
        
        # Check against filename only
        if fnmatch.fnmatch(filename.lower(), pattern_lower):
            return True
            
        # Check against full path (normalize path separators)
        full_path = str(path).replace('\\', '/').lower()
        if fnmatch.fnmatch(full_path, pattern_lower):
            return True
            
        # For patterns with path separators, check path components
        if '/' in pattern:
            # Remove leading slash if present for relative matching
            relative_path = full_path.lstrip('/')
            if fnmatch.fnmatch(relative_path, pattern_lower):
                return True
            
            # Also check against path parts
            path_parts = relative_path.split('/')
            if len(path_parts) >= 2:
                # Check last N components where N = pattern depth
                pattern_parts = pattern_lower.split('/')
                if len(pattern_parts) <= len(path_parts):
                    suffix_path = '/'.join(path_parts[-len(pattern_parts):])
                    if fnmatch.fnmatch(suffix_path, pattern_lower):
                        return True
    
    return False

def is_sensitive_file(filepath, sensitive_patterns, project_root=None, use_gitignore=False):
    """Check if a file path should be blocked based on sensitive patterns and optionally gitignore."""
    if not filepath:
        return False, None
    
    # Check sensitive patterns first
    if matches_pattern(filepath, sensitive_patterns):
        return True, "File matches sensitive pattern"
    
    # Check git ignore if enabled and we have a project root
    if use_gitignore and project_root and is_git_ignored(filepath, project_root):
        return True, "File is git-ignored"
    
    return False, None

def check_bash_command(command, sensitive_patterns, project_root=None, use_gitignore=False):
    """
    Check if a bash command should be blocked.
    Returns (should_block, reason)
    """
    if not command:
        return False, None
    
    # Extract potential file references from command
    # Simple approach - look for file-like arguments
    import shlex
    try:
        tokens = shlex.split(command)
    except ValueError:
        # If shlex fails, fall back to simple split
        tokens = command.split()
    
    # Check if any tokens match sensitive patterns
    for token in tokens:
        # Skip flags and options
        if token.startswith('-') or '=' in token:
            continue
            
        # Check if this looks like a file path
        if '/' in token or '.' in token:
            is_sensitive, reason = is_sensitive_file(token, sensitive_patterns, project_root, use_gitignore)
            if is_sensitive:
                return True, f"Command references sensitive file: {token}"
    
    # Legacy terraform-specific patterns for backward compatibility
    direct_access_patterns = [
        r'(^|[;&|])\s*(cat|less|more|head|tail|nano|vim|vi|emacs|grep|awk|sed|cut)\s+[^|]*terraform\.tfvars',
        r'(^|[;&|])\s*(cat|less|more|head|tail|nano|vim|vi|emacs|grep|awk|sed|cut)\s+[^|]*\.auto\.tfvars',
        # Block copying or moving tfvars files
        r'(cp|mv|rsync|scp).*terraform\.tfvars',
        r'(cp|mv|rsync|scp).*\.auto\.tfvars',
        # Block redirecting tfvars content
        r'terraform\.tfvars.*(>|>>)',
        r'\.auto\.tfvars.*(>|>>)',
    ]
    
    for pattern in direct_access_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Direct access to sensitive files is restricted"
    
    # ALLOW terraform commands with -var-file (legitimate usage)
    # These patterns are explicitly allowed:
    # - terraform plan/apply/destroy/validate -var-file=*.tfvars
    # - terragrunt with var-files
    
    return False, None

def process_tool_input(data, sensitive_patterns, project_root=None, use_gitignore=False):
    """
    Process the tool input and determine if it should be blocked.
    Returns (should_block, error_message)
    """
    hook_event = data.get('hook_event_name', '')
    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    
    # Only process PreToolUse events
    if hook_event != 'PreToolUse':
        return False, None
    
    # Handle different tools
    if tool_name in ['Read', 'Edit', 'Write']:
        # Single file operations
        file_path = tool_input.get('file_path', '')
        is_sensitive, reason = is_sensitive_file(file_path, sensitive_patterns, project_root, use_gitignore)
        if is_sensitive:
            return True, f"Direct access to '{file_path}' is restricted for security reasons.\n   {reason}: This file contains sensitive data."
    
    elif tool_name == 'Grep':
        # Grep can have single path or multiple paths
        paths = []
        if 'path' in tool_input:
            paths.append(tool_input['path'])
        if 'paths' in tool_input:
            paths.extend(tool_input.get('paths', []))
        
        for path in paths:
            is_sensitive, reason = is_sensitive_file(path, sensitive_patterns, project_root, use_gitignore)
            if is_sensitive:
                return True, f"Direct access to '{path}' is restricted for security reasons.\n   {reason}."
    
    elif tool_name == 'MultiEdit':
        # Check all files in the edit list
        edits = tool_input.get('edits', [])
        for edit in edits:
            file_path = edit.get('file_path', '')
            is_sensitive, reason = is_sensitive_file(file_path, sensitive_patterns, project_root, use_gitignore)
            if is_sensitive:
                return True, f"Direct access to '{file_path}' is restricted for security reasons.\n   {reason}."
    
    elif tool_name == 'Bash':
        # Check bash commands more carefully
        command = tool_input.get('command', '')
        should_block, reason = check_bash_command(command, sensitive_patterns, project_root, use_gitignore)
        if should_block:
            return True, f"❌ BLOCKED: {reason}\n   Command attempted: {command}\n   Use appropriate tools or terraform commands for legitimate usage."
    
    return False, None

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Claude Code sensitive file blocker hook')
        parser.add_argument('--git-ignore', action='store_true', 
                          help='Also filter files based on .gitignore patterns')
        
        # Parse known args to allow for other arguments we don't care about
        args, _ = parser.parse_known_intermixed_args()
        
        # Find project root and load patterns
        project_root = find_project_root()
        sensitive_patterns = load_sensitive_patterns(project_root)
        
        # Read JSON input from stdin
        input_data = sys.stdin.read()
        data = json.loads(input_data)
        
        # Process the tool input
        should_block, error_message = process_tool_input(
            data, sensitive_patterns, project_root, args.git_ignore
        )
        
        if should_block:
            print(f"❌ BLOCKED: {error_message}", file=sys.stderr)
            sys.exit(2)  # Block with message
        
        # Allow the action
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        # If we can't parse the JSON, allow the action (fail open)
        print(f"Warning: Could not parse input JSON: {e}", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        # On any other error, log but allow (fail open)
        print(f"Warning: Hook error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == '__main__':
    main()