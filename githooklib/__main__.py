import sys
import fire

from .cli import CLI


def main() -> None:
    cli = CLI()
    exit_code = fire.Fire(cli)
    if isinstance(exit_code, int):
        sys.exit(exit_code)
    sys.exit(0)


if __name__ == "__main__":
    main()
