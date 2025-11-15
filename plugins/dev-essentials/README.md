# Dev Essentials Plugin

Essential development tools, code review agents, and productivity commands for all programming languages.

## Features

### Commands

- `/refactor` - Analyze code and suggest refactoring improvements
- `/test` - Generate comprehensive test cases and test code
- `/doc` - Generate documentation for code (inline, markdown, JSDoc, docstrings)

### Agents

- `code-reviewer` - Comprehensive code review for quality, security, and performance
- `debugger` - Debugging assistant for systematic bug analysis and fixing

## Installation

```bash
/plugin install dev-essentials@personal-security-tools
```

## Usage

### Refactor Code

```bash
/refactor scope=file target=src/utils/helpers.js focus=maintainability
```

### Generate Tests

```bash
/test target=calculateTax framework=jest coverage=unit
```

### Generate Documentation

```bash
/doc target=UserService format=JSDoc
```

### Use the Code Reviewer Agent

The code-reviewer agent provides comprehensive analysis of:
- Code quality and maintainability
- Security vulnerabilities
- Performance issues
- Best practices for the specific language
- Testing coverage

### Use the Debugger Agent

The debugger agent helps with:
- Systematic bug analysis
- Root cause identification
- Fix recommendations
- Prevention strategies

## Supported Languages

This plugin works with all programming languages including:
- JavaScript/TypeScript
- Python
- Java/Kotlin
- C#/F#
- Go
- Rust
- Ruby
- PHP
- And many more...

## Key Benefits

- **Language-agnostic**: Works with any programming language
- **Comprehensive**: Covers code quality, security, performance
- **Actionable**: Provides specific fixes, not just identification
- **Educational**: Explains the reasoning behind recommendations
- **Practical**: Focuses on real-world issues and solutions

## License

MIT
