---
description: Generate a Godot node script with GDScript
---

Create a Godot node script with the following specifications:

Node type: {{node_type}} (Node2D, Node3D, Control, CharacterBody2D, etc.)
Script name: {{script_name}}
Purpose: {{purpose}}

Guidelines:
1. Extend the appropriate Godot node type
2. Include class_name declaration if needed
3. Add @export variables for inspector customization
4. Implement relevant lifecycle methods (_ready, _process, _physics_process)
5. Include proper signal definitions and connections
6. Add comments explaining functionality
7. Follow GDScript naming conventions (PascalCase for classes, snake_case for functions)
8. Include input handling if applicable
9. Add node references using @onready
10. Implement proper resource management

Create the script following Godot best practices.
