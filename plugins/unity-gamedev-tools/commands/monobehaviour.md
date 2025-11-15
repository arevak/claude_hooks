---
description: Generate a Unity MonoBehaviour C# script
---

Create a Unity MonoBehaviour script with the following specifications:

Script name: {{script_name}}
Purpose: {{purpose}}
Component type: {{component_type}} (Player, Enemy, Manager, UI, etc.)

Guidelines:
1. Inherit from MonoBehaviour
2. Use [SerializeField] for inspector-exposed private fields
3. Implement relevant Unity lifecycle methods (Awake, Start, Update, FixedUpdate, OnEnable, OnDisable)
4. Add proper XML documentation comments
5. Follow Unity C# naming conventions (PascalCase for public, camelCase for private)
6. Include null checks for component references
7. Use GetComponent<T>() appropriately
8. Implement cleanup in OnDestroy if needed
9. Add [RequireComponent] attribute if dependencies exist
10. Consider using interfaces for better architecture

Unity Lifecycle Order:
- Awake() - Initialize references
- OnEnable() - Subscribe to events
- Start() - Initialize state
- FixedUpdate() - Physics
- Update() - Per-frame logic
- LateUpdate() - After all updates
- OnDisable() - Unsubscribe from events
- OnDestroy() - Cleanup

Create the MonoBehaviour script following Unity best practices.
