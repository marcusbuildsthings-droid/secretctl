# secretctl

Cross-platform secret storage CLI for AI agents and developers. Store secrets in the OS keychain without cloud sync or biometrics.

## Installation

```bash
pip install secretctl
```

On Linux, install with keyring support:
```bash
pip install secretctl[linux]
```

## Quick Start

```bash
# Store a secret
secretctl set API_KEY sk-xxx123

# Retrieve a secret
secretctl get API_KEY

# List all secrets
secretctl list

# Delete a secret
secretctl delete API_KEY
```

## Commands

### Basic Operations

```bash
secretctl set <name> <value>     # Store a secret
secretctl get <name>             # Retrieve a secret
secretctl delete <name>          # Delete a secret
secretctl list                   # List all secret names
secretctl exists <name>          # Check if secret exists
```

### Import/Export

```bash
# Export to env file
secretctl export > secrets.env
secretctl export --format json > secrets.json

# Import from file
secretctl import secrets.env
secretctl import secrets.json --format json
secretctl import secrets.env --overwrite  # Replace existing
```

### Namespaces

Use different accounts/namespaces to organize secrets:

```bash
secretctl --account myapp set DB_URL "postgres://..."
secretctl --account myapp list
```

## JSON Output

All commands support `--json` for machine-readable output:

```bash
secretctl --json get API_KEY
```

```json
{
  "name": "API_KEY",
  "value": "sk-xxx123",
  "success": true
}
```

## Platform Support

| Platform | Backend | Notes |
|----------|---------|-------|
| macOS | Keychain | Uses `security` command |
| Linux | keyring | Requires `secretctl[linux]` |

## For AI Agents

See [SKILL.md](SKILL.md) for agent-optimized documentation.

## Why secretctl?

- **No cloud sync** - Secrets stay local
- **No biometrics** - Works in automation/CI
- **Simple CLI** - Easy for agents to use
- **JSON output** - Machine-readable
- **Namespaced** - Multiple accounts/apps

## License

MIT
