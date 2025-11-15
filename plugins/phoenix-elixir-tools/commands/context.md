---
description: Generate a Phoenix context with schemas and migrations
---

Create a new Phoenix context with the following specifications:

Context name: {{context_name}}
Schema name: {{schema_name}}
Fields: {{fields}}

Guidelines:
1. Use `mix phx.gen.context` patterns
2. Create context module with proper functions (list, get, create, update, delete)
3. Generate Ecto schema with proper types and validations
4. Include migration file with appropriate field types
5. Add associations if specified
6. Include changesets with validations
7. Follow Elixir naming conventions (PascalCase for modules, snake_case for functions)
8. Add @doc and @spec for public functions
9. Include proper error handling with {:ok, result} and {:error, changeset} tuples

Create the context following Phoenix conventions.
