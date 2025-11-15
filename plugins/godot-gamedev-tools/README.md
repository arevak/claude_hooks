# Godot GameDev Tools Plugin

Development tools for Godot game engine projects using GDScript and C#.

## Features

### Commands

- `/node` - Generate Godot node scripts with GDScript
- `/autoload` - Create autoload singleton scripts for global game systems

### Agents

- `godot-reviewer` - Code review agent specialized in Godot engine best practices

## Installation

```bash
/plugin install godot-gamedev-tools@personal-security-tools
```

## Usage

### Generate a Node Script

```bash
/node node_type=CharacterBody2D script_name=Player purpose="Player character with movement and jumping"
```

### Create an Autoload Singleton

```bash
/autoload singleton_name=GameManager purpose="Manage game state and scene transitions"
```

### Use the Godot Reviewer Agent

The godot-reviewer agent automatically analyzes Godot code for:
- GDScript best practices and patterns
- Node lifecycle usage
- Performance optimizations
- Memory management
- Common Godot pitfalls

## Supported Godot Versions

- Godot 4.x (primary)
- Godot 3.x (compatible with adjustments)

## Requirements

- Godot 4.0+
- Basic understanding of GDScript or C#

## License

MIT
