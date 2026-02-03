"""Backend implementations for secret storage."""

import platform
import subprocess
from abc import ABC, abstractmethod


class SecretBackend(ABC):
    """Abstract base class for secret storage backends."""

    def __init__(self, account: str):
        self.account = account

    @abstractmethod
    def get(self, name: str) -> str | None:
        """Get a secret value."""
        pass

    @abstractmethod
    def set(self, name: str, value: str) -> None:
        """Set a secret value."""
        pass

    @abstractmethod
    def delete(self, name: str) -> None:
        """Delete a secret."""
        pass

    @abstractmethod
    def list(self) -> list[str]:
        """List all secret names."""
        pass


class MacOSKeychain(SecretBackend):
    """macOS Keychain backend using security command."""

    def get(self, name: str) -> str | None:
        """Get a secret from macOS Keychain."""
        try:
            result = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-a", self.account,
                    "-s", name,
                    "-w",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def set(self, name: str, value: str) -> None:
        """Set a secret in macOS Keychain."""
        # Delete existing first (security doesn't update in place)
        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-a", self.account,
                "-s", name,
            ],
            capture_output=True,
        )
        # Add new
        result = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-a", self.account,
                "-s", name,
                "-w", value,
                "-U",  # Update if exists
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to store secret: {result.stderr}")

    def delete(self, name: str) -> None:
        """Delete a secret from macOS Keychain."""
        result = subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-a", self.account,
                "-s", name,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "could not be found" not in result.stderr:
            raise RuntimeError(f"Failed to delete secret: {result.stderr}")

    def list(self) -> list[str]:
        """List all secrets for this account in macOS Keychain."""
        result = subprocess.run(
            ["security", "dump-keychain"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []

        secrets = []
        current_account = None
        current_service = None

        for line in result.stdout.splitlines():
            line = line.strip()
            if '"acct"' in line and f'"{self.account}"' in line:
                current_account = self.account
            elif '"svce"' in line and current_account:
                # Extract service name
                # Format: "svce"<blob>="service_name"
                if '="' in line:
                    current_service = line.split('="')[1].rstrip('"')
                    secrets.append(current_service)
                    current_account = None
                    current_service = None

        return list(set(secrets))  # Deduplicate


class LinuxKeyring(SecretBackend):
    """Linux keyring backend using the keyring library."""

    def __init__(self, account: str):
        super().__init__(account)
        try:
            import keyring
            self.keyring = keyring
        except ImportError:
            raise RuntimeError(
                "keyring library required on Linux. "
                "Install with: pip install secretctl[linux]"
            )

    def get(self, name: str) -> str | None:
        """Get a secret from Linux keyring."""
        return self.keyring.get_password(self.account, name)

    def set(self, name: str, value: str) -> None:
        """Set a secret in Linux keyring."""
        self.keyring.set_password(self.account, name, value)

    def delete(self, name: str) -> None:
        """Delete a secret from Linux keyring."""
        try:
            self.keyring.delete_password(self.account, name)
        except self.keyring.errors.PasswordDeleteError:
            pass  # Already deleted or doesn't exist

    def list(self) -> list[str]:
        """List all secrets (not easily supported on Linux keyring)."""
        # Linux keyring doesn't have a native list function
        # This is a limitation - users need to track their own keys
        return []


def get_backend(account: str) -> SecretBackend:
    """Get the appropriate backend for the current platform."""
    system = platform.system()
    
    if system == "Darwin":
        return MacOSKeychain(account)
    elif system == "Linux":
        return LinuxKeyring(account)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
