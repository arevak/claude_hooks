---
description: Create a Unity ScriptableObject for data-driven design
---

Create a Unity ScriptableObject with the following specifications:

ScriptableObject name: {{so_name}}
Data type: {{data_type}} (Config, Item, Ability, etc.)

Guidelines:
1. Inherit from ScriptableObject
2. Add [CreateAssetMenu] attribute with appropriate menu path
3. Use [SerializeField] for data fields
4. Include proper XML documentation
5. Add validation logic if needed
6. Consider using nested classes for complex data
7. Implement ISerializationCallbackReceiver if needed
8. Add helper methods for data access
9. Use [Header] and [Tooltip] attributes for better inspector UX
10. Consider runtime vs editor-only data

Common ScriptableObject Use Cases:
- Game configuration and settings
- Item/weapon/ability definitions
- Audio/visual effect data
- Level/wave configurations
- Event systems
- Shared data between scenes

Create the ScriptableObject for data-driven game design.
