# Personal Plugin Marketplace for Claude Code

A personal marketplace for Claude Code plugins covering security, productivity, web development, game development, and infrastructure.

## Quick Start

### Add this marketplace to Claude Code

```bash
# Using GitHub
/plugin marketplace add arevak/claudeplugins

# Using Git URL
/plugin marketplace add https://github.com/arevak/claudeplugins.git

# Using local path (for development)
/plugin marketplace add /path/to/claude_hooks
```

### Browse and Install Plugins

```bash
# Browse all available plugins
/plugin

# Install a specific plugin
/plugin install <plugin-name>@personal-security-tools
```

## Available Plugins (7 total)

### 🔒 Sensitive File Blocker
**Category:** Security | **Version:** 1.0.0

Blocks Claude Code access to sensitive files based on configurable patterns and optional .gitignore filtering.

**Features:**
- Pattern-based file blocking using `.sensitive` file
- Optional .gitignore integration
- Prevents accidental exposure of credentials and secrets

**Installation:** `/plugin install sensitive-file-blocker@personal-security-tools`

[📖 Documentation](plugins/sensitive-file-blocker/README.md)

---

### 🛠️ Dev Essentials
**Category:** Productivity | **Version:** 1.0.0

Essential development tools for all programming languages including code review, refactoring, testing, and documentation generation.

**Features:**
- Commands: `/refactor`, `/test`, `/doc`
- Agents: `code-reviewer`, `debugger`
- Language-agnostic productivity tools

**Installation:** `/plugin install dev-essentials@personal-security-tools`

[📖 Documentation](plugins/dev-essentials/README.md)

---

### ⚛️ React TypeScript Tools
**Category:** Development | **Version:** 1.0.0

Development tools and helpers for React and TypeScript projects.

**Features:**
- Commands: `/component`, `/hook`
- Agent: `react-reviewer`
- Component and hook generation with best practices

**Installation:** `/plugin install react-typescript-tools@personal-security-tools`

[📖 Documentation](plugins/react-typescript-tools/README.md)

---

### 🔮 Phoenix Elixir Tools
**Category:** Development | **Version:** 1.0.0

Development tools for Phoenix Framework and Elixir/Erlang projects.

**Features:**
- Commands: `/context`, `/liveview`
- Agent: `elixir-reviewer`
- Phoenix context and LiveView generation

**Installation:** `/plugin install phoenix-elixir-tools@personal-security-tools`

[📖 Documentation](plugins/phoenix-elixir-tools/README.md)

---

### 🎮 Godot GameDev Tools
**Category:** Game Development | **Version:** 1.0.0

Development tools for Godot game engine projects using GDScript.

**Features:**
- Commands: `/node`, `/autoload`
- Agent: `godot-reviewer`
- GDScript node and singleton generation

**Installation:** `/plugin install godot-gamedev-tools@personal-security-tools`

[📖 Documentation](plugins/godot-gamedev-tools/README.md)

---

### 🎯 Unity GameDev Tools
**Category:** Game Development | **Version:** 1.0.0

Development tools for Unity game engine projects using C#.

**Features:**
- Commands: `/monobehaviour`, `/scriptableobject`
- Agent: `unity-reviewer`
- Unity component and data structure generation

**Installation:** `/plugin install unity-gamedev-tools@personal-security-tools`

[📖 Documentation](plugins/unity-gamedev-tools/README.md)

---

### 🏗️ OpenTofu Tools
**Category:** Infrastructure | **Version:** 1.0.0

Development tools for OpenTofu/Terraform infrastructure as code projects.

**Features:**
- Commands: `/module`, `/workflow`
- Agent: `iac-reviewer`
- IaC module generation and workflow automation

**Installation:** `/plugin install opentofu-tools@personal-security-tools`

[📖 Documentation](plugins/opentofu-tools/README.md)

---

## Plugin Categories

- **Security (1):** Sensitive File Blocker
- **Productivity (1):** Dev Essentials
- **Development (2):** React TypeScript Tools, Phoenix Elixir Tools
- **Game Development (2):** Godot GameDev Tools, Unity GameDev Tools
- **Infrastructure (1):** OpenTofu Tools

## Marketplace Structure

```
.
├── .claude-plugin/
│   └── marketplace.json          # Marketplace definition
├── plugins/
│   ├── sensitive-file-blocker/   # Security plugin
│   ├── dev-essentials/           # Productivity plugin
│   ├── react-typescript-tools/   # React/TS plugin
│   ├── phoenix-elixir-tools/     # Phoenix/Elixir plugin
│   ├── godot-gamedev-tools/      # Godot plugin
│   ├── unity-gamedev-tools/      # Unity plugin
│   └── opentofu-tools/           # OpenTofu/Terraform plugin
├── src/
│   └── claude_hooks/             # Source code for development
└── tests/                        # Test suite
```

## For Team Distribution

To automatically install this marketplace for your team, add it to `.claude/settings.json` in your project:

```json
{
  "extraKnownMarketplaces": {
    "personal-security-tools": {
      "source": {
        "source": "github",
        "repo": "arevak/claudeplugins"
      }
    }
  },
  "enabledPlugins": [
    "sensitive-file-blocker@personal-security-tools",
    "dev-essentials@personal-security-tools"
  ]
}
```

When team members trust the repository folder, Claude Code will automatically:
1. Install the marketplace
2. Enable the specified plugins

## Development

### Project Structure

- **`src/claude_hooks/`** - Source code for plugin development
- **`plugins/`** - Packaged plugins for distribution
- **`tests/`** - Test suite for plugins
- **`.claude-plugin/`** - Marketplace configuration

### Testing Locally

```bash
# Add local marketplace for testing
/plugin marketplace add .

# Install plugin from local marketplace
/plugin install <plugin-name>@personal-security-tools

# Run tests
uv run pytest
```

### Adding New Plugins

1. Create a new directory in `plugins/`
2. Add `plugin.json` manifest
3. Add plugin implementation (hooks, commands, agents, etc.)
4. Update `.claude-plugin/marketplace.json` with the new plugin entry
5. Document in plugin README.md
6. Test locally before publishing

## Contributing

Contributions are welcome! To add a plugin:

1. Fork this repository
2. Create a new plugin in the `plugins/` directory
3. Update the marketplace.json
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Resources

- [Claude Code Plugins Documentation](https://docs.claude.com/en/plugins)
- [Plugin Marketplace Guide](https://docs.claude.com/en/plugin-marketplaces)
- [Plugin Development Reference](https://docs.claude.com/en/plugins-reference)

## Marketplace Metadata

- **Name:** personal-security-tools
- **Version:** 1.0.0
- **Owner:** Personal Plugin Collection
- **Total Plugins:** 7
- **Categories:** Security, Productivity, Development, Game Development, Infrastructure
