# React TypeScript Tools Plugin

Development tools and helpers for React and TypeScript projects.

## Features

### Commands

- `/component` - Generate React components with TypeScript
- `/hook` - Create custom React hooks with proper typing

### Agents

- `react-reviewer` - Code review agent specialized in React and TypeScript best practices

## Installation

```bash
/plugin install react-typescript-tools@personal-security-tools
```

## Usage

### Generate a Component

```bash
/component component_name=UserProfile component_type=functional include_tests=yes
```

### Create a Custom Hook

```bash
/hook hook_name=useDebounce purpose="Debounce user input"
```

### Use the React Reviewer Agent

The react-reviewer agent automatically analyzes React and TypeScript code for:
- Hook usage and dependencies
- TypeScript type safety
- Performance optimizations
- Accessibility
- Best practices

## Requirements

- React 16.8+ (for hooks support)
- TypeScript 4.0+
- Node.js 14+

## License

MIT
