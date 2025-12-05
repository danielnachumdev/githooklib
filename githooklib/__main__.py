import sys

from .cli import HookCLI


def main():
    cli = HookCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

