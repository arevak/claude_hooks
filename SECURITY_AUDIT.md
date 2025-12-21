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

## 🔴 CRITICAL: Vulnerability #4 - AWK Script Injection & File Indirection

**Location:** `src/claude_hooks/block_sensitive.py:134-192`

**Issue:** AWK is an extremely powerful scripting language with multiple methods to access files that are invisible to token-based parsing. The hook only checks command-line arguments, not AWK script content.

### AWK Bypass Methods

#### 4a. Variable Indirection
```bash
awk -v file=.env '{getline < file; print}' /dev/null
```
**Why it bypasses:** The filename `.env` is assigned to a variable, not a command-line token. The hook sees `file=.env` and skips it because it contains `=`.

**Proof:**
```
TEST 8: awk with -v variable assignment
Command: awk -v file=.env "{getline < file; print}" /dev/null
Blocked: False
❌ VULNERABILITY: awk with variable indirection bypasses!
```

#### 4b. Inline File Reading (getline)
```bash
awk 'BEGIN {while(getline < ".env") print}'
```
**Why it bypasses:** The filename is embedded inside the AWK script string, completely invisible to external tokenization.

**Proof:**
```
TEST 9: awk reading file in script
Command: awk "BEGIN {while(getline < ".env") print}"
Blocked: False
❌ VULNERABILITY: awk inline file reading bypasses!
```

#### 4c. System Command Injection
```bash
awk 'BEGIN {system("cat .env")}'
awk 'BEGIN {system("find . -name *.tfvars | xargs cat")}'
```
**Why it bypasses:** AWK's `system()` function executes arbitrary shell commands. The nested command is invisible to the hook.

**Proof:**
```
TEST 10: awk system() command injection
Command: awk "BEGIN {system("cat .env")}"
Blocked: False
❌ VULNERABILITY: awk system() command injection!
```

**Impact:** AWK provides multiple independent bypass mechanisms. An attacker can read any sensitive file using AWK scripting features.

**Additional AWK Attack Vectors:**
```bash
# Print specific fields from sensitive files
awk -F'=' '/PASSWORD/ {print $2}' .env

# Read multiple sensitive files in one command
awk 'FNR==1{print FILENAME":"$0}' .env config.yml secrets.json

# Use AWK as a full programming language to exfiltrate data
awk 'BEGIN {
  while((getline line < ".env") > 0)
    print line | "base64"
}'
```

---

## 🔴 CRITICAL: Vulnerability #5 - Ripgrep Without Path

**Location:** `src/claude_hooks/block_sensitive.py:134-192` (Bash command checking)

**Issue:** Same as Grep vulnerability - ripgrep (rg) without a path searches recursively from the current directory, but the hook doesn't detect this unless sensitive filenames appear in the arguments.

**Exploit:**
```bash
rg "password" --type yaml
rg "API_KEY" --type env
rg "secret" --iglob "!node_modules/*"
```

**Proof:**
```
TEST 2: rg recursive without path
Command: rg "password" --type yaml
Blocked: False
❌ VULNERABILITY: ripgrep searches all files!
```

**Why it bypasses:** The command contains no explicit file paths in tokens - just `--type yaml` which doesn't look like a file. Ripgrep searches all YAML files recursively by default.

**Impact:** Ripgrep is faster than grep and commonly used. This bypass allows searching all files matching a type without detection.

**Additional Ripgrep Bypasses:**
```bash
# Search with file type filters
rg "SECRET_KEY" --type-add 'custom:*.{env,tfvars}' --type custom

# Search with complex globs
rg "password" --glob "**/*.{yml,yaml,json}" --glob "!**/node_modules/**"

# Output only matching content, no filenames
rg "API_KEY" --no-filename --no-line-number
```

---

## Updated Attack Scenarios

### Scenario 4: AWK-Based Data Exfiltration
```bash
# Extract all environment variables
awk 'BEGIN {while(getline < ".env") print}' | base64

# Parse and extract specific secrets
awk -F'=' '/PASSWORD|SECRET|KEY/ {print $2}' .env secrets.yml

# Use system() to chain multiple commands
awk 'BEGIN {system("find . -name *.tfvars -exec cat {} \\;")}'

# Read file via variable indirection to evade detection
awk -v f=terraform.tfvars 'BEGIN {while(getline < f) print}'
```

### Scenario 5: Ripgrep Reconnaissance
```bash
# Find all potential secret files without specifying paths
rg "password|secret|key" --type yaml --type json

# Search for AWS keys across entire codebase
rg "AKIA[0-9A-Z]{16}" --no-filename

# Search with type definitions that avoid detection
rg "secret" --type-add 'secrets:*.{env,tfvars,yml}' --type secrets
```

---

## Additional Recommended Fixes

### Fix #6: AWK Script Analysis (CRITICAL)

**Location:** `src/claude_hooks/block_sensitive.py:134-192`

AWK is too dangerous to parse safely. Recommended approach: **Block AWK entirely** or implement strict allowlist mode.

```python
def check_bash_command(command, sensitive_spec, project_root=None, use_gitignore=False):
    if not command:
        return False, None

    # CRITICAL: Block AWK entirely for high-security environments
    # AWK has too many ways to access files: getline, system(), variable indirection
    tokens = shlex.split(command) if command else []
    cmd_name = tokens[0] if tokens else ''

    if cmd_name in ['awk', 'gawk', 'mawk', 'nawk']:
        # Check if AWK script contains dangerous constructs
        if 'getline' in command or 'system(' in command:
            return True, "AWK scripts with 'getline' or 'system()' are not allowed for security reasons."

        # Parse -v variable assignments
        for i, token in enumerate(tokens):
            if token == '-v' and i + 1 < len(tokens):
                # Extract variable assignment: -v file=.env
                assignment = tokens[i + 1]
                if '=' in assignment:
                    _, value = assignment.split('=', 1)
                    is_sensitive, reason = is_sensitive_file(value, sensitive_spec, project_root, use_gitignore)
                    if is_sensitive:
                        return True, f"AWK variable references sensitive file: {value}"

    # Rest of checks...
```

**Alternative:** Strict mode blocks AWK entirely:
```python
if strict_mode and cmd_name in ['awk', 'gawk', 'mawk', 'nawk']:
    return True, "AWK is disabled in strict security mode."
```

### Fix #7: Ripgrep Path Validation

**Location:** `src/claude_hooks/block_sensitive.py:134-192`

```python
def check_bash_command(command, sensitive_spec, project_root=None, use_gitignore=False):
    # ...

    cmd_name = tokens[0] if tokens else ''

    if cmd_name in ['rg', 'ripgrep']:
        # Check if ripgrep has explicit paths or searches from root
        has_path = any(not token.startswith('-') and '/' in token for token in tokens[1:])

        if not has_path:
            # Searching without explicit path - potentially dangerous
            return True, "Ripgrep without explicit path is not allowed. Specify a safe directory to search."

        # Check --type and --glob flags for sensitive patterns
        for i, token in enumerate(tokens):
            if token in ['--type', '-t', '--glob', '-g'] and i + 1 < len(tokens):
                pattern = tokens[i + 1]
                if matches_pattern(pattern, sensitive_spec):
                    return True, f"Ripgrep pattern '{pattern}' matches sensitive files"

    # Rest of checks...
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
| AWK variable indirection | **CRITICAL** | Easy | Complete bypass |
| AWK getline injection | **CRITICAL** | Easy | Complete bypass |
| AWK system() injection | **CRITICAL** | Trivial | Complete bypass + RCE |
| Ripgrep without path | **CRITICAL** | Trivial | Complete bypass |
| Flag value parsing | **MEDIUM** | Easy | Partial bypass |
| Recursive grep | **MEDIUM** | Trivial | Data exposure |

---

## Conclusion

The `block_sensitive` hook has **7 critical security vulnerabilities** that can be trivially exploited to bypass all sensitive file protections. The vulnerabilities span multiple attack vectors:

- **Tool-level bypasses:** Grep and Ripgrep without paths
- **Shell-level bypasses:** Command/process substitution
- **Scripting-level bypasses:** AWK variable indirection, getline, and system() injection

AWK is particularly dangerous because it's a full programming language with multiple file access methods and arbitrary command execution capabilities.

Immediate remediation is required before this hook can be considered secure.

**Recommended Actions (Priority Order):**
1. **CRITICAL:** Implement Fix #2 (Block command/process substitution) - Prevents $(…) and <(…) bypasses
2. **CRITICAL:** Implement Fix #6 (AWK script analysis or blocking) - AWK is extremely dangerous
3. **CRITICAL:** Implement Fix #1 (Grep path validation) - Applies to both grep and ripgrep
4. **CRITICAL:** Implement Fix #7 (Ripgrep path validation) - Same issue as grep
5. **HIGH:** Implement Fix #3 (Parse flag values) - Catches --flag=value syntax
6. **MEDIUM:** Add comprehensive regression tests for all bypasses
7. **MEDIUM:** Security review of all fixes
8. **LOW:** Consider strict allowlist mode (Fix #5) for high-security environments

---

**Audited by:** Claude Code Security Analysis
**Date:** 2025-12-21
