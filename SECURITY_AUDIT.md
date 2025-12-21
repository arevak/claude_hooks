# Security Audit: block_sensitive Hook Vulnerabilities

**Date:** 2025-12-21
**Severity:** HIGH
**Status:** CRITICAL VULNERABILITIES CONFIRMED

## Executive Summary

The `block_sensitive` hook has **critical security vulnerabilities** that allow attackers to bypass sensitive file protection through:
1. **Grep tool calls without path parameters** (100% bypass)
2. **Bash command substitution** `$(...)` (100% bypass)
3. **Bash process substitution** `<(...)` (100% bypass)

These bypasses completely defeat the purpose of the sensitive file protection mechanism.

---

## Vulnerability Details

### 🔴 CRITICAL: Vulnerability #1 - Grep Without Path Parameter

**Location:** `src/claude_hooks/block_sensitive.py:223-234`

**Issue:** The Grep tool handler only checks if a `path` parameter exists. When no path is provided, Grep searches the current directory recursively, but the hook allows it.

**Code:**
```python
elif tool_name == 'Grep':
    paths = []
    if 'path' in tool_input:
        paths.append(tool_input['path'])
    # ...
    for path in paths:  # Empty list if no 'path' key!
        is_sensitive, reason = is_sensitive_file(path, ...)
```

**Exploit:**
```python
Grep(pattern="API_KEY")  # Searches entire directory tree
Grep(pattern="password", type="py")  # Searches all Python files
```

**Proof:**
```
TEST 1: Grep without path parameter
----------------------------------------
Command: Grep(pattern="API_KEY", type="py") [no path]
Blocked: False
❌ VULNERABILITY: Grep without path bypasses all checks!
```

**Impact:** Complete bypass of all sensitive file protection for Grep operations.

---

### 🔴 CRITICAL: Vulnerability #2 - Command Substitution Bypass

**Location:** `src/claude_hooks/block_sensitive.py:134-192`

**Issue:** The bash command checker uses static tokenization with `shlex.split()`. Command substitution `$(...)` is evaluated at runtime by the shell, making the actual file paths invisible to the hook.

**Code:**
```python
def check_bash_command(command, ...):
    tokens = shlex.split(command)  # Only sees static tokens!
    for token in tokens:
        if '/' in token or '.' in token:
            # Check token...
```

**Exploit:**
```bash
cat $(find . -name ".env")
grep "secret" $(find . -name "*.tfvars")
base64 $(find secrets/ -type f)
```

**Proof:**
```
TEST 4: Command substitution
----------------------------------------
Command: cat $(find . -name ".env")
Blocked: False
❌ VULNERABILITY: Command substitution bypasses detection!
```

**Impact:** Attacker can access any sensitive file using dynamic command substitution.

---

### 🔴 CRITICAL: Vulnerability #3 - Process Substitution Bypass

**Location:** Same as #2

**Issue:** Process substitution `<(...)` creates a temporary file descriptor that's expanded by the shell, not visible to static analysis.

**Exploit:**
```bash
grep "password" <(find . -name "*.env")
cat <(find secrets/ -type f | head -1)
diff <(cat secret1.tfvars) <(cat secret2.tfvars)
```

**Proof:**
```
TEST 5: Process substitution
----------------------------------------
Command: grep "password" <(find . -name "*.env")
Blocked: False
❌ VULNERABILITY: Process substitution bypasses detection!
```

**Impact:** Complete bypass using process substitution syntax.

---

## Partially Mitigated Threats

### 🟡 MEDIUM: find | xargs - DETECTED ✅

**Status:** Currently blocked by token analysis

```
TEST 2: find | xargs cat
----------------------------------------
Command: find . -name "*.tfvars" | xargs cat
Blocked: True ✅
```

The hook detects `*.tfvars` as a token and blocks it.

### 🟡 MEDIUM: find -exec - DETECTED ✅

**Status:** Currently blocked by token analysis

```
TEST 3: find -exec cat
----------------------------------------
Command: find . -name "*.env" -exec cat {} \;
Blocked: True ✅
```

The hook detects `*.env` as a token and blocks it.

**However:** These protections are fragile and can be bypassed with variations like:
- Using variables: `EXT=".env"; find . -name "*$EXT" -exec cat {} \;`
- Indirect patterns: `find . -type f | grep "\.env$" | xargs cat`

---

## Additional Security Concerns

### Token Filtering Issues

**Location:** `src/claude_hooks/block_sensitive.py:161-169`

```python
for token in tokens:
    if token.startswith('-') or '=' in token:
        continue  # Skip flags and options
```

**Issue:** This skips tokens containing `=`, which means:
```bash
somecommand --file=secret.tfvars  # BYPASSED: token contains '='
```

**Mitigation:** Parse `--flag=value` syntax and extract the value for checking.

### Recursive Grep Without Path

While Grep without a path is a vulnerability, even if a path is provided, recursive searches can expose sensitive files in subdirectories:

```python
Grep(pattern="secret", path=".", output_mode="content")  # Searches everything
```

**Recommendation:** Consider requiring explicit paths or blocking searches from project root.

---

## Attack Scenarios

### Scenario 1: Data Exfiltration
```bash
# Attacker uses command substitution to read .env file
cat $(find . -name ".env") | base64

# Process substitution to grep secrets
grep -r "password" <(find . -type f)
```

### Scenario 2: Credential Harvesting
```python
# Use Grep without path to search for AWS keys
Grep(pattern="AKIA[0-9A-Z]{16}")  # Searches entire project

# Search for private keys
Grep(pattern="BEGIN PRIVATE KEY", type="pem")
```

### Scenario 3: Terraform Secrets Access
```bash
# Command substitution bypasses tfvars protection
terraform show -json $(find . -name "terraform.tfstate")

# Process substitution to view variables
cat <(find . -name "*.auto.tfvars")
```

---

## Recommended Fixes

### Fix #1: Grep Path Validation (CRITICAL)

**Location:** `src/claude_hooks/block_sensitive.py:223-234`

```python
elif tool_name == 'Grep':
    paths = []
    if 'path' in tool_input:
        path = tool_input['path']
        if path:  # Only add non-empty paths
            paths.append(path)
        else:
            # Empty path defaults to '.'
            paths.append('.')
    else:
        # No path parameter - defaults to current directory
        paths.append('.')

    # Now check all paths including default '.'
    for path in paths:
        is_sensitive, reason = is_sensitive_file(path, sensitive_spec, project_root, use_gitignore)
        if is_sensitive:
            return True, f"Direct access to '{path}' is restricted for security reasons.\n   {reason}."

        # Also check if searching from project root with sensitive subdirectories
        if path in ['.', '', '/'] and has_sensitive_patterns(sensitive_spec):
            return True, "Recursive grep from project root is restricted when sensitive patterns are configured. Please specify a safe subdirectory."
```

### Fix #2: Detect Command/Process Substitution (CRITICAL)

**Location:** `src/claude_hooks/block_sensitive.py:134-192`

Add early detection before tokenization:

```python
def check_bash_command(command, sensitive_spec, project_root=None, use_gitignore=False):
    if not command:
        return False, None

    # CRITICAL: Block command and process substitution
    if '$(' in command or '`' in command:
        return True, "Command substitution $() or backticks are not allowed for security reasons."

    if '<(' in command or '>(' in command:
        return True, "Process substitution <() is not allowed for security reasons."

    # Rest of existing checks...
```

### Fix #3: Parse Flag Values

**Location:** `src/claude_hooks/block_sensitive.py:161-169`

```python
for token in tokens:
    # Parse --flag=value syntax
    if '=' in token and (token.startswith('--') or token.startswith('-')):
        _, value = token.split('=', 1)
        if '/' in value or '.' in value:
            is_sensitive, reason = is_sensitive_file(value, sensitive_spec, project_root, use_gitignore)
            if is_sensitive:
                return True, f"Command references sensitive file: {value}"
        continue

    if token.startswith('-'):
        continue  # Skip other flags

    # Existing path check...
```

### Fix #4: Find Command Analysis

Add specific detection for `find` commands:

```python
def analyze_find_command(command, sensitive_spec):
    """Analyze find commands for sensitive pattern matches."""
    # Extract -name, -path, -iname, -ipath arguments
    find_patterns = re.findall(r'-(?:i?name|i?path)\s+["\']?([^"\s]+)["\']?', command)

    for pattern in find_patterns:
        # Check if pattern would match sensitive files
        if matches_pattern(pattern, sensitive_spec):
            return True, f"Find pattern '{pattern}' matches sensitive files"

    return False, None
```

### Fix #5: Implement Allowlist Mode

For high-security environments:

```python
# In .sensitive file:
# @mode strict
# Only allow specific safe commands
```

```python
if strict_mode:
    allowed_commands = ['terraform', 'git', 'npm', 'pytest']
    cmd_name = tokens[0] if tokens else ''
    if cmd_name not in allowed_commands:
        return True, f"Command '{cmd_name}' not in allowlist"
```

---

## Testing Recommendations

1. **Add regression tests** for all bypass scenarios
2. **Fuzz test** with various shell syntax combinations
3. **Test edge cases** like unicode, escaped characters, null bytes
4. **Verify fixes** don't break legitimate use cases (terraform -var-file, git operations)

---

## Severity Assessment

| Vulnerability | Severity | Exploitability | Impact |
|---------------|----------|----------------|--------|
| Grep without path | **CRITICAL** | Trivial | Complete bypass |
| Command substitution | **CRITICAL** | Easy | Complete bypass |
| Process substitution | **CRITICAL** | Easy | Complete bypass |
| Flag value parsing | **MEDIUM** | Easy | Partial bypass |
| Recursive grep | **MEDIUM** | Trivial | Data exposure |

---

## Conclusion

The `block_sensitive` hook has **critical security vulnerabilities** that can be trivially exploited to bypass all sensitive file protections. Immediate remediation is required before this hook can be considered secure.

**Recommended Action:**
1. Implement Fix #1 (Grep validation) - CRITICAL
2. Implement Fix #2 (Block substitution) - CRITICAL
3. Add comprehensive test coverage
4. Security review of all fixes
5. Document secure usage patterns

---

**Audited by:** Claude Code Security Analysis
**Date:** 2025-12-21
