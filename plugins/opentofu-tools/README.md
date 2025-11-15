# OpenTofu Tools Plugin

Development tools for OpenTofu and Terraform infrastructure as code projects.

## Features

### Commands

- `/module` - Generate OpenTofu/Terraform modules with best practices
- `/workflow` - Execute OpenTofu workflows (init, plan, apply, destroy)

### Agents

- `iac-reviewer` - Code review agent specialized in IaC security and best practices

## Installation

```bash
/plugin install opentofu-tools@personal-security-tools
```

## Usage

### Generate a Module

```bash
/module module_name=vpc resources="VPC, Subnets, Route Tables" provider=AWS
```

### Execute Workflow

```bash
/workflow action=plan environment=staging auto_approve=no
```

### Use the IaC Reviewer Agent

The iac-reviewer agent automatically analyzes OpenTofu/Terraform code for:
- Security vulnerabilities and misconfigurations
- Best practices and patterns
- State management issues
- Performance optimizations
- Cloud provider specific recommendations

## Supported Providers

- AWS
- Azure
- Google Cloud Platform
- And 100+ other Terraform providers

## Requirements

- OpenTofu 1.6+ or Terraform 1.5+
- Cloud provider CLI tools (optional)
- Appropriate cloud credentials configured

## Security Notes

This plugin works alongside the sensitive-file-blocker plugin to:
- Prevent direct access to `.tfvars` files containing secrets
- Enforce secure credential management
- Protect state files with sensitive data

Always use:
- Environment variables for secrets
- Terraform Cloud/Enterprise for state storage
- Vault or secret managers for sensitive values

## License

MIT
