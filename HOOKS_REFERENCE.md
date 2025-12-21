# Hooks reference

> This page provides reference documentation for implementing hooks in Claude Code.

<Tip>
  For a quickstart guide with examples, see [Get started with Claude Code hooks](/en/hooks-guide).
</Tip>

## Configuration

Claude Code hooks are configured in your [settings files](/en/settings):

* `~/.claude/settings.json` - User settings
* `.claude/settings.json` - Project settings
* `.claude/settings.local.json` - Local project settings (not committed)
* Enterprise managed policy settings

<Note>
  Enterprise administrators can use `allowManagedHooksOnly` to block user, project, and plugin hooks. See [Hook configuration](/en/settings#hook-configuration).
</Note>

### Structure

Hooks are organized by matchers, where each matcher can have multiple hooks:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

* **matcher**: Pattern to match tool names, case-sensitive (only applicable for
  `PreToolUse`, `PermissionRequest`, and `PostToolUse`)
  * Simple strings match exactly: `Write` matches only the Write tool
  * Supports regex: `Edit|Write` or `Notebook.*`
  * Use `*` to match all tools. You can also use empty string (`""`) or leave
    `matcher` blank.
* **hooks**: Array of hooks to execute when the pattern matches
  * `type`: Hook execution type - `"command"` for bash commands or `"prompt"` for LLM-based evaluation
  * `command`: (For `type: "command"`) The bash command to execute (can use `$CLAUDE_PROJECT_DIR` environment variable)
  * `prompt`: (For `type: "prompt"`) The prompt to send to the LLM for evaluation
  * `timeout`: (Optional) How long a hook should run, in seconds, before canceling that specific hook

For events like `UserPromptSubmit`, `Stop`, and `SubagentStop`
that don't use matchers, you can omit the matcher field:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/prompt-validator.py"
          }
        ]
      }
    ]
  }
}
```

### Project-Specific Hook Scripts

You can use the environment variable `CLAUDE_PROJECT_DIR` (only available when
Claude Code spawns the hook command) to reference scripts stored in your project,
ensuring they work regardless of Claude's current directory:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
          }
        ]
      }
    ]
  }
}
```

### Plugin hooks

[Plugins](/en/plugins) can provide hooks that integrate seamlessly with your user and project hooks. Plugin hooks are automatically merged with your configuration when plugins are enabled.

**How plugin hooks work**:

* Plugin hooks are defined in the plugin's `hooks/hooks.json` file or in a file given by a custom path to the `hooks` field.
* When a plugin is enabled, its hooks are merged with user and project hooks
* Multiple hooks from different sources can respond to the same event
* Plugin hooks use the `${CLAUDE_PLUGIN_ROOT}` environment variable to reference plugin files

**Example plugin hook configuration**:

```json
{
  "description": "Automatic code formatting",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

<Note>
  Plugin hooks use the same format as regular hooks with an optional `description` field to explain the hook's purpose.
</Note>

<Note>
  Plugin hooks run alongside your custom hooks. If multiple hooks match an event, they all execute in parallel.
</Note>

**Environment variables for plugins**:

* `${CLAUDE_PLUGIN_ROOT}`: Absolute path to the plugin directory
* `${CLAUDE_PROJECT_DIR}`: Project root directory (same as for project hooks)
* All standard environment variables are available

See the [plugin components reference](/en/plugins-reference#hooks) for details on creating plugin hooks.

## Prompt-Based Hooks

In addition to bash command hooks (`type: "command"`), Claude Code supports prompt-based hooks (`type: "prompt"`) that use an LLM to evaluate whether to allow or block an action. Prompt-based hooks are currently only supported for `Stop` and `SubagentStop` hooks, where they enable intelligent, context-aware decisions.

### How prompt-based hooks work

Instead of executing a bash command, prompt-based hooks:

1. Send the hook input and your prompt to a fast LLM (Haiku)
2. The LLM responds with structured JSON containing a decision
3. Claude Code processes the decision automatically

### Configuration

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if Claude should stop: $ARGUMENTS. Check if all tasks are complete."
          }
        ]
      }
    ]
  }
}
```

**Fields:**

* `type`: Must be `"prompt"`
* `prompt`: The prompt text to send to the LLM
  * Use `$ARGUMENTS` as a placeholder for the hook input JSON
  * If `$ARGUMENTS` is not present, input JSON is appended to the prompt
* `timeout`: (Optional) Timeout in seconds (default: 30 seconds)

### Response schema

The LLM must respond with JSON containing:

```json
{
  "decision": "approve" | "block",
  "reason": "Explanation for the decision",
  "continue": false,  // Optional: stops Claude entirely
  "stopReason": "Message shown to user",  // Optional: custom stop message
  "systemMessage": "Warning or context"  // Optional: shown to user
}
```

**Response fields:**

* `decision`: `"approve"` allows the action, `"block"` prevents it
* `reason`: Explanation shown to Claude when decision is `"block"`
* `continue`: (Optional) If `false`, stops Claude's execution entirely
* `stopReason`: (Optional) Message shown when `continue` is false
* `systemMessage`: (Optional) Additional message shown to the user

### Supported hook events

Prompt-based hooks work with any hook event, but are most useful for:

* **Stop**: Intelligently decide if Claude should continue working
* **SubagentStop**: Evaluate if a subagent has completed its task
* **UserPromptSubmit**: Validate user prompts with LLM assistance
* **PreToolUse**: Make context-aware permission decisions
* **PermissionRequest**: Intelligently allow or deny permission dialogs

### Example: Intelligent Stop hook

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You are evaluating whether Claude should stop working. Context: $ARGUMENTS\n\nAnalyze the conversation and determine if:\n1. All user-requested tasks are complete\n2. Any errors need to be addressed\n3. Follow-up work is needed\n\nRespond with JSON: {\"decision\": \"approve\" or \"block\", \"reason\": \"your explanation\"}",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Example: SubagentStop with custom logic

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if this subagent should stop. Input: $ARGUMENTS\n\nCheck if:\n- The subagent completed its assigned task\n- Any errors occurred that need fixing\n- Additional context gathering is needed\n\nReturn: {\"decision\": \"approve\" or \"block\", \"reason\": \"explanation\"}"
          }
        ]
      }
    ]
  }
}
```

### Comparison with bash command hooks

| Feature               | Bash Command Hooks      | Prompt-Based Hooks             |
| --------------------- | ----------------------- | ------------------------------ |
| **Execution**         | Runs bash script        | Queries LLM                    |
| **Decision logic**    | You implement in code   | LLM evaluates context          |
| **Setup complexity**  | Requires script file    | Configure prompt               |
| **Context awareness** | Limited to script logic | Natural language understanding |
| **Performance**       | Fast (local execution)  | Slower (API call)              |
| **Use case**          | Deterministic rules     | Context-aware decisions        |

### Best practices

* **Be specific in prompts**: Clearly state what you want the LLM to evaluate
* **Include decision criteria**: List the factors the LLM should consider
* **Test your prompts**: Verify the LLM makes correct decisions for your use cases
* **Set appropriate timeouts**: Default is 30 seconds, adjust if needed
* **Use for complex decisions**: Bash hooks are better for simple, deterministic rules

See the [plugin components reference](/en/plugins-reference#hooks) for details on creating plugin hooks.

## Hook Events

### PreToolUse

Runs after Claude creates tool parameters and before processing the tool call.

**Common matchers:**

* `Task` - Subagent tasks (see [subagents documentation](/en/sub-agents))
* `Bash` - Shell commands
* `Glob` - File pattern matching
* `Grep` - Content search
* `Read` - File reading
* `Edit` - File editing
* `Write` - File writing
* `WebFetch`, `WebSearch` - Web operations

Use [PreToolUse decision control](#pretooluse-decision-control) to allow, deny, or ask for permission to use the tool.

### PermissionRequest

Runs when the user is shown a permission dialog.
Use [PermissionRequest decision control](#permissionrequest-decision-control) to allow or deny on behalf of the user.

Recognizes the same matcher values as PreToolUse.

### PostToolUse

Runs immediately after a tool completes successfully.

Recognizes the same matcher values as PreToolUse.

### Notification

Runs when Claude Code sends notifications. Supports matchers to filter by notification type.

**Common matchers:**

* `permission_prompt` - Permission requests from Claude Code
* `idle_prompt` - When Claude is waiting for user input (after 60+ seconds of idle time)
* `auth_success` - Authentication success notifications
* `elicitation_dialog` - When Claude Code needs input for MCP tool elicitation

You can use matchers to run different hooks for different notification types, or omit the matcher to run hooks for all notifications.

**Example: Different notifications for different types**

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/permission-alert.sh"
          }
        ]
      },
      {
        "matcher": "idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/idle-notification.sh"
          }
        ]
      }
    ]
  }
}
```

### UserPromptSubmit

Runs when the user submits a prompt, before Claude processes it. This allows you
to add additional context based on the prompt/conversation, validate prompts, or
block certain types of prompts.

### Stop

Runs when the main Claude Code agent has finished responding. Does not run if
the stoppage occurred due to a user interrupt.

### SubagentStop

Runs when a Claude Code subagent (Task tool call) has finished responding.

### PreCompact

Runs before Claude Code is about to run a compact operation.

**Matchers:**

* `manual` - Invoked from `/compact`
* `auto` - Invoked from auto-compact (due to full context window)

### SessionStart

Runs when Claude Code starts a new session or resumes an existing session (which
currently does start a new session under the hood). Useful for loading in
development context like existing issues or recent changes to your codebase, installing dependencies, or setting up environment variables.

**Matchers:**

* `startup` - Invoked from startup
* `resume` - Invoked from `--resume`, `--continue`, or `/resume`
* `clear` - Invoked from `/clear`
* `compact` - Invoked from auto or manual compact.

#### Persisting environment variables

SessionStart hooks have access to the `CLAUDE_ENV_FILE` environment variable, which provides a file path where you can persist environment variables for subsequent bash commands.

**Example: Setting individual environment variables**

```bash
#!/bin/bash

if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export API_KEY=your-api-key' >> "$CLAUDE_ENV_FILE"
  echo 'export PATH="$PATH:./node_modules/.bin"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

**Example: Persisting all environment changes from the hook**

When your setup modifies the environment (for example, `nvm use`), capture and persist all changes by diffing the environment:

```bash
#!/bin/bash

ENV_BEFORE=$(export -p | sort)

# Run your setup commands that modify the environment
source ~/.nvm/nvm.sh
nvm use 20

if [ -n "$CLAUDE_ENV_FILE" ]; then
  ENV_AFTER=$(export -p | sort)
  comm -13 <(echo "$ENV_BEFORE") <(echo "$ENV_AFTER") >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

Any variables written to this file will be available in all subsequent bash commands that Claude Code executes during the session.

<Note>
  `CLAUDE_ENV_FILE` is only available for SessionStart hooks. Other hook types do not have access to this variable.
</Note>

### SessionEnd

Runs when a Claude Code session ends. Useful for cleanup tasks, logging session
statistics, or saving session state.

The `reason` field in the hook input will be one of:

* `clear` - Session cleared with /clear command
* `logout` - User logged out
* `prompt_input_exit` - User exited while prompt input was visible
* `other` - Other exit reasons

## Hook Input

Hooks receive JSON data via stdin containing session information and
event-specific data:

```typescript
{
  // Common fields
  session_id: string
  transcript_path: string  // Path to conversation JSON
  cwd: string              // The current working directory when the hook is invoked
  permission_mode: string  // Current permission mode: "default", "plan", "acceptEdits", or "bypassPermissions"

  // Event-specific fields
  hook_event_name: string
  ...
}
```

### PreToolUse Input

The exact schema for `tool_input` depends on the tool.

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

### PostToolUse Input

The exact schema for `tool_input` and `tool_response` depends on the tool.

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

### Notification Input

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "notification_type": "permission_prompt"
}
```

### UserPromptSubmit Input

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate the factorial of a number"
}
```

### Stop and SubagentStop Input

`stop_hook_active` is true when Claude Code is already continuing as a result of
a stop hook. Check this value or process the transcript to prevent Claude Code
from running indefinitely.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```

### PreCompact Input

For `manual`, `custom_instructions` comes from what the user passes into
`/compact`. For `auto`, `custom_instructions` is empty.

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "permission_mode": "default",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```

### SessionStart Input

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "permission_mode": "default",
  "hook_event_name": "SessionStart",
  "source": "startup"
}
```

### SessionEnd Input

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../00893aaf-19fa-41d2-8238-13269b9b3ca0.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionEnd",
  "reason": "exit"
}
```

## Hook Output

There are two mutually exclusive ways for hooks to return output back to Claude Code. The output
communicates whether to block and any feedback that should be shown to Claude
and the user.

### Simple: Exit Code

Hooks communicate status through exit codes, stdout, and stderr:

* **Exit code 0**: Success. `stdout` is shown to the user in verbose mode
  (ctrl+o), except for `UserPromptSubmit` and `SessionStart`, where stdout is
  added to the context. JSON output in `stdout` is parsed for structured control
  (see [Advanced: JSON Output](#advanced-json-output)).
* **Exit code 2**: Blocking error. Only `stderr` is used as the error message
  and fed back to Claude. The format is `[command]: {stderr}`. JSON in `stdout`
  is **not** processed for exit code 2. See per-hook-event behavior below.
* **Other exit codes**: Non-blocking error. `stderr` is shown to the user in verbose mode (ctrl+o) with
  format `Failed with non-blocking status code: {stderr}`. If `stderr` is empty,
  it shows `No stderr output`. Execution continues.

<Warning>
  Reminder: Claude Code does not see stdout if the exit code is 0, except for
  the `UserPromptSubmit` hook where stdout is injected as context.
</Warning>

#### Exit Code 2 Behavior

| Hook Event          | Behavior                                                           |
| ------------------- | ------------------------------------------------------------------ |
| `PreToolUse`        | Blocks the tool call, shows stderr to Claude                       |
| `PermissionRequest` | Denies the permission, shows stderr to Claude                      |
| `PostToolUse`       | Shows stderr to Claude (tool already ran)                          |
| `Notification`      | N/A, shows stderr to user only                                     |
| `UserPromptSubmit`  | Blocks prompt processing, erases prompt, shows stderr to user only |
| `Stop`              | Blocks stoppage, shows stderr to Claude                            |
| `SubagentStop`      | Blocks stoppage, shows stderr to Claude subagent                   |
| `PreCompact`        | N/A, shows stderr to user only                                     |
| `SessionStart`      | N/A, shows stderr to user only                                     |
| `SessionEnd`        | N/A, shows stderr to user only                                     |

### Advanced: JSON Output

Hooks can return structured JSON in `stdout` for more sophisticated control. (Content truncated for length - this is the hooks reference documentation provided by the user)
