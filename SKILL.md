# secretctl Skill

Cross-platform secret storage CLI with JSON output for AI agents.

## Prerequisites

- macOS or Linux
- Python 3.9+
- On Linux: `pip install secretctl[linux]`

## Installation

```bash
pip install secretctl
```

## Command Reference

| Command | Description |
|---------|-------------|
| `secretctl set <name> <value>` | Store a secret |
| `secretctl get <name>` | Retrieve a secret |
| `secretctl delete <name>` | Delete a secret |
| `secretctl list` | List all secret names |
| `secretctl exists <name>` | Check if secret exists |
| `secretctl export` | Export all secrets |
| `secretctl import <file>` | Import secrets from file |

## JSON Output

**Always use `--json` flag for automation:**

```bash
secretctl --json <command>
```

All responses include `"success": true|false`.

## Common Patterns

### Store and Retrieve
```bash
# Store
secretctl --json set API_KEY "sk-xxx123"
# Returns: {"name": "API_KEY", "stored": true, "account": "secretctl"}

# Retrieve
secretctl --json get API_KEY
# Returns: {"name": "API_KEY", "value": "sk-xxx123", "success": true}
```

### Check Before Use
```bash
secretctl --json exists API_KEY
# Returns: {"name": "API_KEY", "exists": true}
```

### List All Secrets
```bash
secretctl --json list
# Returns: {"secrets": ["API_KEY", "DB_URL"], "count": 2, "account": "secretctl"}
```

### Namespaced Secrets
```bash
# Store under different accounts
secretctl --json --account myapp set DB_URL "postgres://..."
secretctl --json --account myapp list
```

### Bulk Operations
```bash
# Export
secretctl export --format json > /tmp/secrets.json

# Import
secretctl import /tmp/secrets.json --format json --overwrite
```

## Error Handling

Errors return non-zero exit code and JSON:
```json
{"error": "Secret not found: MISSING_KEY", "success": false}
```

## Security Notes

- macOS: Uses login keychain (no biometrics required)
- Linux: Uses system keyring (may require unlock)
- Secrets stored locally, no cloud sync
- Use `--account` for namespace isolation

## Exit Codes

- `0` - Success
- `1` - Error (details in JSON/stderr)
