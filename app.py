# ENTRY POINT (START OF SERVER)

from crypto_cli.api import crypto_cli as app
from crypto_cli.cli import cli

if __name__ == "__main__":
    cli()