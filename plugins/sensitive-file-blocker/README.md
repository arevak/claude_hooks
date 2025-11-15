# Sensitive File Blocker Plugin

A Claude Code plugin that blocks access to sensitive files based on configurable patterns and optional .gitignore filtering.

## Features

- **Pattern-based blocking**: Define sensitive file patterns in a `.sensitive` file
- **.gitignore integration**: Optionally block access to git-ignored files
- **Multiple tool coverage**: Blocks Read, Edit, Write, Bash, Grep, and Glob operations
- **Flexible pattern matching**: Supports wildcards and path-based patterns
- **Security-focused**: Prevents accidental exposure of credentials, secrets, and sensitive data

## Installation

Install this plugin from the marketplace:

```bash
/plugin install sensitive-file-blocker@personal-security-tools
```

## Configuration

### 1. Create a `.sensitive` file

In your project root, create a `.sensitive` file with patterns of files to block:

```
# Sensitive configuration files
*.tfvars
*.auto.tfvars
.env
.env.*
credentials.json
secrets.yaml

# API keys and tokens
**/api-keys/**
**/secrets/**

# Private keys
*.pem
*.key
id_rsa*
```

### 2. Enable .gitignore filtering (optional)

To also block access to git-ignored files, the plugin supports the `--git-ignore` flag. You can configure this in your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Edit|MultiEdit|Bash|Grep|Glob|Write",
        "hooks": [
          {
            "type": "command",
            "command": "block-sensitive.py --git-ignore"
          }
        ]
      }
    ]
  }
}
```

## How It Works

The plugin intercepts file operations before they execute and checks:

1. **Pattern matching**: Does the file match any pattern in `.sensitive`?
2. **.gitignore check** (if enabled): Is the file ignored by git?

If either check matches, the operation is blocked with a clear error message.

## Pattern Syntax

The `.sensitive` file supports gitignore-style patterns:

- `*.tfvars` - Match any .tfvars file
- `secrets/` - Match the secrets directory
- `**/api-keys/**` - Match api-keys directory anywhere
- `.env.*` - Match .env files with any extension
- `*.pem` - Match PEM certificate files

## Blocked Operations

The plugin blocks these Claude Code tools when they access sensitive files:

- **Read**: Reading file contents
- **Edit**: Editing files
- **MultiEdit**: Batch editing multiple files
- **Write**: Writing/creating files
- **Bash**: Commands that reference sensitive files
- **Grep**: Searching in sensitive files
- **Glob**: File pattern matching

## Example Usage

```bash
# This will be blocked if .env matches a pattern
/read .env

# This will be blocked if terraform.tfvars is in .sensitive
/edit terraform.tfvars

# Bash commands referencing sensitive files are also blocked
cat secrets.json
```

## Troubleshooting

### Plugin not blocking files

1. Verify the `.sensitive` file exists in your project root
2. Check that patterns are correctly formatted (no leading/trailing spaces)
3. Ensure the plugin is enabled: `/plugin list`

### False positives

If legitimate files are being blocked:

1. Review your `.sensitive` patterns for overly broad matches
2. Consider being more specific with path-based patterns
3. Comment out patterns with `#` to test

### .gitignore filtering not working

1. Ensure you're using the `--git-ignore` flag
2. Verify you're in a git repository
3. Test with `git check-ignore <filename>` to see if git recognizes the pattern

## License

MIT License - See LICENSE file for details
