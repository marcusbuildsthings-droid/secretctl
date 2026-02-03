"""Main CLI entry point for secretctl."""

import json
import sys
import click

from . import __version__
from .backend import get_backend


class Context:
    """Shared context for all commands."""

    def __init__(self, json_output: bool = False, account: str = "secretctl"):
        self.json_output = json_output
        self.account = account
        self.backend = get_backend(account)

    def output(self, data: dict | list | str, success: bool = True):
        """Output data in the appropriate format."""
        if self.json_output:
            if isinstance(data, str):
                data = {"message": data, "success": success}
            elif isinstance(data, dict) and "success" not in data:
                data = {**data, "success": success}
            click.echo(json.dumps(data, indent=2))
        else:
            if isinstance(data, dict):
                for key, value in data.items():
                    if key != "success":
                        click.echo(f"{key}: {value}")
            elif isinstance(data, list):
                for item in data:
                    click.echo(item)
            else:
                click.echo(data)

    def error(self, message: str, exit_code: int = 1):
        """Output an error message and exit."""
        if self.json_output:
            click.echo(json.dumps({"error": message, "success": False}))
        else:
            click.echo(f"Error: {message}", err=True)
        sys.exit(exit_code)


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("--account", "-a", default="secretctl", help="Account/namespace for secrets")
@click.version_option(version=__version__, prog_name="secretctl")
@click.pass_context
def main(ctx, json_output: bool, account: str):
    """Cross-platform secret storage CLI for AI agents.

    Store and retrieve secrets from the OS keychain without cloud sync
    or biometrics. Designed for automation and AI agent workflows.

    Examples:
        secretctl set API_KEY sk-xxx
        secretctl get API_KEY
        secretctl list
    """
    ctx.obj = Context(json_output=json_output, account=account)


@main.command()
@click.argument("name")
@click.argument("value")
@pass_context
def set(ctx, name: str, value: str):
    """Store a secret.

    Example:
        secretctl set API_KEY sk-xxx123
        secretctl set DATABASE_URL "postgres://user:pass@host/db"
    """
    try:
        ctx.backend.set(name, value)
        ctx.output({"name": name, "stored": True, "account": ctx.account})
    except Exception as e:
        ctx.error(f"Failed to store secret: {e}")


@main.command()
@click.argument("name")
@pass_context
def get(ctx, name: str):
    """Retrieve a secret.

    Example:
        secretctl get API_KEY
    """
    try:
        value = ctx.backend.get(name)
        if value is None:
            ctx.error(f"Secret not found: {name}")
        ctx.output({"name": name, "value": value})
    except Exception as e:
        ctx.error(f"Failed to retrieve secret: {e}")


@main.command()
@click.argument("name")
@pass_context
def delete(ctx, name: str):
    """Delete a secret.

    Example:
        secretctl delete API_KEY
    """
    try:
        ctx.backend.delete(name)
        ctx.output({"name": name, "deleted": True})
    except Exception as e:
        ctx.error(f"Failed to delete secret: {e}")


@main.command("list")
@pass_context
def list_secrets(ctx):
    """List all secret names (values hidden).

    Example:
        secretctl list
    """
    try:
        secrets = ctx.backend.list()
        ctx.output({"secrets": secrets, "count": len(secrets), "account": ctx.account})
    except Exception as e:
        ctx.error(f"Failed to list secrets: {e}")


@main.command()
@click.argument("name")
@pass_context
def exists(ctx, name: str):
    """Check if a secret exists.

    Example:
        secretctl exists API_KEY
    """
    try:
        value = ctx.backend.get(name)
        exists = value is not None
        ctx.output({"name": name, "exists": exists})
    except Exception as e:
        ctx.error(f"Failed to check secret: {e}")


@main.command()
@click.option("--file", "-f", "output_file", help="Output file (default: stdout)")
@click.option("--format", "fmt", type=click.Choice(["env", "json"]), default="env", help="Export format")
@pass_context
def export(ctx, output_file: str | None, fmt: str):
    """Export all secrets.

    Example:
        secretctl export > secrets.env
        secretctl export --format json > secrets.json
    """
    try:
        secrets = ctx.backend.list()
        data = {}
        for name in secrets:
            value = ctx.backend.get(name)
            if value:
                data[name] = value

        if fmt == "json":
            output = json.dumps(data, indent=2)
        else:  # env format
            output = "\n".join(f'{k}="{v}"' for k, v in data.items())

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            ctx.output({"exported": len(data), "file": output_file, "format": fmt})
        else:
            click.echo(output)
    except Exception as e:
        ctx.error(f"Failed to export secrets: {e}")


@main.command("import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["env", "json"]), default="env", help="Import format")
@click.option("--overwrite", is_flag=True, help="Overwrite existing secrets")
@pass_context
def import_secrets(ctx, input_file: str, fmt: str, overwrite: bool):
    """Import secrets from file.

    Example:
        secretctl import secrets.env
        secretctl import secrets.json --format json --overwrite
    """
    try:
        with open(input_file, "r") as f:
            content = f.read()

        if fmt == "json":
            data = json.loads(content)
        else:  # env format
            data = {}
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Strip quotes if present
                    value = value.strip().strip('"').strip("'")
                    data[key.strip()] = value

        imported = 0
        skipped = 0
        for name, value in data.items():
            if not overwrite and ctx.backend.get(name) is not None:
                skipped += 1
                continue
            ctx.backend.set(name, value)
            imported += 1

        ctx.output({"imported": imported, "skipped": skipped, "file": input_file})
    except Exception as e:
        ctx.error(f"Failed to import secrets: {e}")


if __name__ == "__main__":
    main()
