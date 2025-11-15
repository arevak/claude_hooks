---
description: Create a Godot autoload singleton script
---

Create a Godot autoload singleton with the following specifications:

Singleton name: {{singleton_name}}
Purpose: {{purpose}}

Guidelines:
1. Create as a static class or singleton pattern
2. Include relevant game state or global functionality
3. Define custom signals for cross-node communication
4. Add configuration variables with @export
5. Implement save/load functionality if needed
6. Include proper initialization in _ready()
7. Add documentation for public methods
8. Consider thread safety if needed
9. Follow singleton best practices (avoid god objects)

Common autoload types:
- GameManager (game state, scene transitions)
- AudioManager (sound effects, music)
- SaveManager (save/load game data)
- EventBus (global event system)

Create the autoload script and provide instructions for adding to Project Settings.
