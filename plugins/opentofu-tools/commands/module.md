---
description: Generate an OpenTofu/Terraform module
---

Create an OpenTofu module with the following specifications:

Module name: {{module_name}}
Resources: {{resources}}
Cloud provider: {{provider}} (AWS, Azure, GCP, etc.)

Guidelines:
1. Create module directory structure (main.tf, variables.tf, outputs.tf)
2. Define input variables with proper types, descriptions, and validation
3. Include output values for important resource attributes
4. Add a versions.tf with required provider versions
5. Create a README.md with usage examples
6. Include a terraform.tfvars.example file
7. Follow naming conventions (lowercase, underscores for multi-word)
8. Add tags/labels for resource organization
9. Implement data sources where appropriate
10. Include lifecycle rules if needed

Module Structure:
```
module-name/
├── main.tf           # Primary resource definitions
├── variables.tf      # Input variable declarations
├── outputs.tf        # Output value definitions
├── versions.tf       # Provider version constraints
├── terraform.tfvars.example  # Example values
└── README.md         # Documentation
```

Best Practices:
- Use meaningful variable names
- Add validation blocks for critical variables
- Output all important resource IDs and attributes
- Include default values where sensible
- Document required vs optional variables

Create the module following OpenTofu/Terraform best practices.
