---
description: Generate test cases and test code
---

Generate comprehensive tests for the following:

Target: {{target}} (function/class/module)
Test framework: {{framework}}
Coverage goal: {{coverage}} (unit/integration/e2e)

Guidelines for Test Generation:
1. **Test Structure**: Follow AAA pattern
   - Arrange: Set up test data and conditions
   - Act: Execute the code being tested
   - Assert: Verify the results

2. **Test Coverage**: Include tests for
   - Happy path scenarios
   - Edge cases
   - Error conditions
   - Boundary values
   - Null/undefined/empty inputs
   - Invalid inputs

3. **Test Types**: Based on coverage goal
   - **Unit tests**: Individual functions/methods
   - **Integration tests**: Component interactions
   - **E2E tests**: Full user workflows

4. **Best Practices**:
   - One assertion per test (when possible)
   - Descriptive test names (describe what is being tested)
   - Independent tests (no test depends on another)
   - Fast execution
   - Deterministic results
   - Mock external dependencies

5. **Test Naming**: Use clear, descriptive names
   - Format: `test_<function>_<scenario>_<expected_result>`
   - Example: `test_user_login_with_invalid_password_returns_error`

Generate complete, runnable test code with proper setup and teardown.
