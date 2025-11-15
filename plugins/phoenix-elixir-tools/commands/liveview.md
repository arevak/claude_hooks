---
description: Generate a Phoenix LiveView component
---

Create a Phoenix LiveView component with the following specifications:

LiveView name: {{liveview_name}}
Purpose: {{purpose}}
Include tests: {{include_tests}} (yes/no)

Guidelines:
1. Create LiveView module with mount/3 and handle_event/3 callbacks
2. Use proper assigns with socket
3. Include HEEx template with proper bindings
4. Add LiveView-specific features (phx-click, phx-submit, etc.)
5. Implement proper PubSub patterns if needed
6. Add form handling with changesets if applicable
7. Include proper error handling and flash messages
8. Follow Phoenix.LiveView best practices
9. If tests requested, create test file using LiveViewTest

Create the LiveView in the appropriate directory following Phoenix structure.
