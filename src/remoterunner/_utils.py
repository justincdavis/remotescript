# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
from __future__ import annotations

import argparse
import logging
from pathlib import Path

_log = logging.getLogger(__name__)


def parse_arguments() -> (
    tuple[Path, Path, Path, list[str], str | None, list[str], str, list[str]]
):
    """
    Parse the arguments and validate data.

    Returns
    -------
    tuple[Path, Path, Path, list[str], str | None, list[str], str, list[str]]
        The parsed and validated arguments.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--script",
        help="The script to execute on remote machines.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--config",
        help="The configuration file to use for the remote machines.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--output",
        help="The output file to aggregate the data into.",
        type=str,
        default="output.json",
    )
    parser.add_argument(
        "--datafiles",
        nargs="+",
        type="list[str]",
        help="Any data files needed.",
    )
    parser.add_argument(
        "--deps",
        type=str,
        help="Required dependencies in the form of a requirements.txt file.",
    )
    parser.add_argument(
        "--dep_scripts",
        nargs="+",
        type="list[str]",
        help="Any dependency scripts needed.",
    )
    parser.add_argument(
        "--time",
        type=str,
        default="python",
        choices=["python", "linux"],
        help="Which method of timing overall execution should be used.",
    )
    parser.add_argument(
        "--remove",
        nargs="+",
        type="list[str]",
        help="Any files which should be removed at the end of execution.",
    )

    args = parser.parse_args()
    input_file_str: str = args.script
    config_file_str: str = args.config
    output_file_str: str = args.output
    datafiles: list[str] = args.datafiles or []
    requirements_file: str | None = args.deps
    deps_scripts: list[str] = args.dep_scripts or []
    time_method: str = args.time
    remove_files: list[str] = args.remove or []

    input_file = Path(input_file_str)
    if not input_file.exists():
        err_msg = f"Input file does not exist: {input_file}"
        raise FileNotFoundError(err_msg)
    if input_file.suffix != ".py":
        err_msg = f"Input file must be a Python script: {input_file}"
        raise ValueError(err_msg)

    config_file = Path(config_file_str)
    if not config_file.exists():
        err_msg = f"Config file does not exist: {config_file}"
        raise FileNotFoundError(err_msg)

    output_file = Path(output_file_str)
    if output_file.exists():
        err_msg = f"Output file already exists: {output_file}"
        err_msg += "\nFile contents will be overwritten."
        _log.warning(err_msg)

    for datafile in datafiles:
        datafile_path = Path(datafile)
        if not datafile_path.exists():
            err_msg = f"Data file does not exist: {datafile_path}"
            raise FileNotFoundError(err_msg)

    if requirements_file is not None:
        requirements_path = Path(requirements_file)
        if not requirements_path.exists():
            err_msg = f"Requirements file does not exist: {requirements_path}"
            raise FileNotFoundError(err_msg)
        if requirements_path.suffix != ".txt":
            err_msg = f"Requirements file must be a text file: {requirements_path}"
            raise ValueError(err_msg)

    for dep_script in deps_scripts:
        dep_script_path = Path(dep_script)
        if not dep_script_path.exists():
            err_msg = f"Dependency script does not exist: {dep_script_path}"
            raise FileNotFoundError(err_msg)
        if dep_script_path.suffix != ".py":
            err_msg = f"Dependency script must be a Python script: {dep_script_path}"
            raise ValueError(err_msg)

    valid_time_methods = ["python", "linux"]
    if time_method not in valid_time_methods:
        err_msg = f"Invalid time method: {time_method},"
        err_msg += f" valid methods are: {valid_time_methods}"
        raise ValueError(err_msg)

    return (
        input_file,
        config_file,
        output_file,
        datafiles,
        requirements_file,
        deps_scripts,
        time_method,
        remove_files,
    )
