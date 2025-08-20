#!/usr/bin/env python3
"""
Test utilities for mocking git and other external dependencies.
"""

import unittest.mock as mock


def mock_git_check_ignore(ignored_files=None, not_a_repo=False, git_not_found=False):
    """
    Create a mock for subprocess.run that simulates git check-ignore behavior.
    
    Args:
        ignored_files: List of file paths that should be treated as ignored
        not_a_repo: If True, simulate being outside a git repository
        git_not_found: If True, simulate git command not being available
    """
    if ignored_files is None:
        ignored_files = []
    
    def _mock_run(cmd, **kwargs):
        # Only mock git commands
        if not (isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == 'git' and cmd[1] == 'check-ignore'):
            return mock.DEFAULT
            
        # Simulate git not found
        if git_not_found:
            raise FileNotFoundError("git command not found")
        
        # Get the file path being checked
        filepath = cmd[2] if len(cmd) > 2 else None
        
        # Create mock result
        result = mock.Mock()
        
        # Simulate not being in a git repository
        if not_a_repo:
            result.returncode = 128
            result.stdout = ""
            result.stderr = "fatal: not a git repository (or any of the parent directories): .git"
            return result
        
        # Check if file should be ignored
        if filepath in ignored_files:
            # File is ignored - git check-ignore returns 0
            result.returncode = 0
            result.stdout = f".gitignore:1:*\t{filepath}\n"
            result.stderr = ""
        else:
            # File is not ignored - git check-ignore returns 1
            result.returncode = 1
            result.stdout = ""
            result.stderr = ""
            
        return result
    
    return _mock_run


def mock_git_check_ignore_with_patterns(pattern_mapping=None, **kwargs):
    """
    Create a more sophisticated mock that maps file patterns to ignore status.
    
    Args:
        pattern_mapping: Dict mapping glob patterns to whether they should be ignored
                        e.g., {"*.log": True, "*.py": False}
    """
    if pattern_mapping is None:
        pattern_mapping = {}
    
    import fnmatch
    
    def _mock_run(cmd, **kwargs_inner):
        # Only mock git commands
        if not (isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == 'git' and cmd[1] == 'check-ignore'):
            return mock.DEFAULT
            
        # Handle special cases (git not found, not a repo)
        base_mock = mock_git_check_ignore(**kwargs)
        if kwargs.get('git_not_found') or kwargs.get('not_a_repo'):
            return base_mock(cmd, **kwargs_inner)
        
        # Get the file path being checked
        filepath = cmd[2] if len(cmd) > 2 else None
        if not filepath:
            result = mock.Mock()
            result.returncode = 1
            result.stdout = ""
            result.stderr = ""
            return result
        
        # Check patterns
        is_ignored = False
        matching_pattern = None
        
        for pattern, should_ignore in pattern_mapping.items():
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filepath.lower(), pattern.lower()):
                is_ignored = should_ignore
                matching_pattern = pattern
                break
        
        # Create result
        result = mock.Mock()
        if is_ignored:
            result.returncode = 0
            result.stdout = f".gitignore:1:{matching_pattern}\t{filepath}\n"
            result.stderr = ""
        else:
            result.returncode = 1
            result.stdout = ""
            result.stderr = ""
            
        return result
    
    return _mock_run


def create_mock_scenarios():
    """Create common mock scenarios for testing."""
    return {
        'typical_ignores': mock_git_check_ignore([
            '*.log',
            'debug.log',
            '/project/node_modules/package.json',
            '/project/.DS_Store',
            '/project/dist/bundle.js',
            '.env',
            'temp.txt'
        ]),
        
        'pattern_based': mock_git_check_ignore_with_patterns({
            '*.log': True,
            '*.env': True,
            '*.DS_Store': True,
            'node_modules/*': True,
            'dist/*': True,
            '*.py': False,
            '*.js': False,
            '*.md': False
        }),
        
        'git_not_found': mock_git_check_ignore(git_not_found=True),
        
        'not_a_repo': mock_git_check_ignore(not_a_repo=True),
        
        'empty_repo': mock_git_check_ignore([])  # Nothing ignored
    }