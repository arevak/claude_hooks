# Phoenix Elixir Tools Plugin

Development tools and helpers for Phoenix Framework and Elixir/Erlang projects.

## Features

### Commands

- `/context` - Generate Phoenix contexts with schemas and migrations
- `/liveview` - Create Phoenix LiveView components

### Agents

- `elixir-reviewer` - Code review agent specialized in Elixir and Phoenix best practices

## Installation

```bash
/plugin install phoenix-elixir-tools@personal-security-tools
```

## Usage

### Generate a Context

```bash
/context context_name=Accounts schema_name=User fields="name:string email:string:unique age:integer"
```

### Create a LiveView

```bash
/liveview liveview_name=UserListLive purpose="Display and manage users" include_tests=yes
```

### Use the Elixir Reviewer Agent

The elixir-reviewer agent automatically analyzes Elixir and Phoenix code for:
- Pattern matching and idiomatic Elixir
- Phoenix context boundaries
- Ecto query optimization
- LiveView best practices
- Error handling patterns

## Requirements

- Phoenix 1.6+
- Elixir 1.13+
- Erlang/OTP 24+

## License

MIT
