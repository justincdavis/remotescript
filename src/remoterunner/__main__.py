# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
from __future__ import annotations

from ._utils import parse_arguments


def main() -> None:
    """
    Run the main program.
    """
    script, config, output, datafiles, deps, dep_scripts = parse_arguments()
    print(script, config, output, datafiles, deps, dep_scripts)


if __name__ == "__main__":
    main()
