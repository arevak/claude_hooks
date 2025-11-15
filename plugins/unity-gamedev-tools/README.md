# Unity GameDev Tools Plugin

Development tools for Unity game engine projects using C#.

## Features

### Commands

- `/monobehaviour` - Generate Unity MonoBehaviour C# scripts
- `/scriptableobject` - Create ScriptableObjects for data-driven design

### Agents

- `unity-reviewer` - Code review agent specialized in Unity engine best practices

## Installation

```bash
/plugin install unity-gamedev-tools@personal-security-tools
```

## Usage

### Generate a MonoBehaviour Script

```bash
/monobehaviour script_name=PlayerController purpose="Handle player movement and input" component_type=Player
```

### Create a ScriptableObject

```bash
/scriptableobject so_name=WeaponData data_type=Item
```

### Use the Unity Reviewer Agent

The unity-reviewer agent automatically analyzes Unity code for:
- MonoBehaviour lifecycle best practices
- Performance optimizations
- Memory management
- Common Unity pitfalls
- Architecture patterns

## Supported Unity Versions

- Unity 2021.x and later (primary)
- Unity 2020.x (compatible)

## Requirements

- Unity Editor 2020.3+
- C# 8.0+
- .NET Standard 2.1

## License

MIT
