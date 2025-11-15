---
description: Analyze and suggest refactoring improvements
---

Analyze the codebase and suggest refactoring improvements:

Scope: {{scope}} (file/directory/function/class)
Target: {{target}}
Focus: {{focus}} (readability/performance/maintainability/all)

Guidelines for Analysis:
1. **Code Smells**: Identify common code smells
   - Long methods/functions
   - Duplicate code
   - Large classes
   - Long parameter lists
   - Divergent change
   - Shotgun surgery

2. **Design Patterns**: Suggest appropriate patterns
   - Identify opportunities for pattern application
   - Recommend refactoring to patterns
   - Suggest pattern replacements

3. **SOLID Principles**: Check adherence to:
   - Single Responsibility Principle
   - Open/Closed Principle
   - Liskov Substitution Principle
   - Interface Segregation Principle
   - Dependency Inversion Principle

4. **Code Quality**: Improve
   - Naming conventions
   - Function/method length
   - Cyclomatic complexity
   - Coupling and cohesion
   - Error handling

5. **Performance**: Optimize
   - Algorithm efficiency
   - Resource usage
   - Caching opportunities
   - Lazy loading
   - Database query optimization

Provide specific, actionable refactoring suggestions with before/after examples.
