# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
"""Run scripts remotely on multiple machines."""

from __future__ import annotations

import logging
from threading import Thread
from typing import TYPE_CHECKING

from ._core import run_script
from ._imports import (
    compare_and_prune_libs,
    generate_requirements,
    parse_and_trim_imports,
)
from ._utils import parse_arguments, parse_config

if TYPE_CHECKING:
    from pathlib import Path

_log = logging.getLogger(__name__)


def main() -> None:
    """Run the main program."""
    (
        script_path,
        config_path,
        output_dir_path,
        datafiles,
        deps,
        dep_scripts,
        dep_dirs,
        timeout,
        use_site_packages,
        no_venv,
    ) = parse_arguments()
    config = parse_config(config_path)

    # generate the output directory
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # generate subdirectory for each machine
    machine_output_dirs: list[Path] = []
    for machine_name, _, _, _, _ in config:
        machine_output_dir: Path = output_dir_path / machine_name
        machine_output_dir.mkdir(parents=True, exist_ok=True)
        machine_output_dirs.append(machine_output_dir)

    # generate requirements file if it does not exist
    if deps is None:
        if (dep_scripts is not None and len(dep_scripts) > 0) or (
            dep_dirs is not None and len(dep_dirs) > 0
        ):
            wstr = "Dependency scripts/directories provided but no requirements file."
            wstr += " Requirements.txt will be auto-generated from ONLY primary script."
            wstr += (
                " Dependency scripts/directories may not get all required libraries."
            )
            _log.warning(wstr)
        _log.warning("Auto-generating requirements file from provided script.")
        imports: list[tuple[str, str]] = parse_and_trim_imports(script_path)
        valid_imports: list[str] = compare_and_prune_libs(imports)
        deps = output_dir_path / "requirements.txt"
        deps.touch()
        deps.write_text(generate_requirements(valid_imports))
        _log.debug(f"Generated requirements file: {deps}")

    # create thread for each machines connection
    threads: list[Thread] = []
    for (machine_name, hostname, user, password, port), m_output_dir in zip(
        config,
        machine_output_dirs,
    ):
        threads.append(
            Thread(
                target=run_script,
                args=(
                    machine_name,
                    hostname,
                    user,
                    password,
                    port,
                    script_path,
                    m_output_dir,
                    deps,
                    datafiles,
                    dep_scripts,
                    dep_dirs,
                    timeout,
                    use_site_packages,
                    no_venv,
                ),
                daemon=True,
            ),
        )
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
