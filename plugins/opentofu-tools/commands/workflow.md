---
description: Execute OpenTofu workflow (init, plan, apply)
---

Execute OpenTofu workflow for infrastructure changes:

Action: {{action}} (plan/apply/destroy)
Environment: {{environment}}
Auto-approve: {{auto_approve}} (yes/no)

Guidelines:
1. Always run `tofu init` first if .terraform directory is missing
2. Use workspace selection for multi-environment setups
3. Generate and review plan before applying
4. Use -var-file for environment-specific variables
5. Enable state locking to prevent concurrent modifications
6. Use -target for selective resource changes (when needed)
7. Create backups before destructive operations
8. Review the plan output carefully
9. Document the changes being made

Workflow Steps:
```bash
# Initialize (if needed)
tofu init

# Select workspace
tofu workspace select {{environment}}

# Plan changes
tofu plan -var-file="{{environment}}.tfvars" -out=plan.tfplan

# Review and apply
tofu show plan.tfplan
tofu apply plan.tfplan

# Or for destroy
tofu destroy -var-file="{{environment}}.tfvars"
```

Safety Checks:
- Always review plan before apply
- Never auto-approve in production without review
- Ensure state backup exists
- Verify correct workspace/environment
- Check for breaking changes

Execute the OpenTofu workflow with appropriate safety measures.
