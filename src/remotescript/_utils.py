# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
from __future__ import annotations

import argparse
import configparser
import json
import logging
import time
from pathlib import Path

_log = logging.getLogger(__name__)


def parse_arguments() -> (
    tuple[
        Path,
        Path,
        Path,
        list[Path],
        Path | None,
        list[Path],
        list[Path],
        int,
        bool,
        bool,
    ]
):
    """
    Parse the arguments and validate data.

    Returns
    -------
    tuple[Path, Path, Path, list[Path], Path | None, list[Path], list[Path], int, bool, bool]
        The parsed and validated arguments.

    Raises
    ------
    FileNotFoundError
        If any of the files do not exist.
    ValueError
        If any of the files are not of the correct type.
        If the time method is not valid.

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
        help="The output directory to aggregate the data into.",
        type=str,
    )
    parser.add_argument(
        "--requirements",
        type=str,
        help="Required dependencies in the form of a requirements.txt file.",
    )
    parser.add_argument(
        "--datafiles",
        nargs="+",
        help="Any data files needed.",
    )
    parser.add_argument(
        "--dep_scripts",
        nargs="+",
        help="Any dependency scripts needed.",
    )
    parser.add_argument(
        "--dep_dirs",
        nargs="+",
        help="Any dependency directories needed.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="The timeout for the connection to the remote machine.",
    )
    parser.add_argument(
        "--system-site-packages",
        action="store_true",
        help="Use the system site packages.",
    )
    parser.add_argument(
        "--no-venv",
        action="store_true",
        help="Do not use a virtual environment.",
    )

    args = parser.parse_args()
    input_file_str: str = args.script
    config_file_str: str = args.config
    output_dir_str: str = args.output or f"output_{int(time.time())}"
    datafiles: list[str] = args.datafiles or []
    requirements_file: str | None = args.requirements
    deps_scripts: list[str] = args.dep_scripts or []
    dep_dirs: list[str] = args.dep_dirs or []
    timeout: int = args.timeout
    use_site_packages: bool = args.system_site_packages
    no_venv: bool = args.no_venv

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

    output_dir = Path(output_dir_str)
    if output_dir.exists():
        if output_dir.is_file():
            err_msg = f"Output directory is a file: {output_dir}"
            raise ValueError(err_msg)
        err_msg = f"Output directory already exists: {output_dir}"
        err_msg += " file contents will be overwritten."
        _log.warning(err_msg)

    datafile_paths: list[Path] = []
    for datafile in datafiles:
        datafile_path = Path(datafile)
        if not datafile_path.exists():
            err_msg = f"Data file does not exist: {datafile_path}"
            raise FileNotFoundError(err_msg)
        datafile_paths.append(datafile_path)

    requirements_retval: Path | None = None
    if requirements_file is not None:
        requirements_path = Path(requirements_file)
        if not requirements_path.exists():
            err_msg = f"Requirements file does not exist: {requirements_path}"
            raise FileNotFoundError(err_msg)
        if requirements_path.suffix != ".txt":
            err_msg = f"Requirements file must be a text file: {requirements_path}"
            raise ValueError(err_msg)
        requirements_retval = requirements_path

    dep_script_paths: list[Path] = []
    for dep_script in deps_scripts:
        dep_script_path = Path(dep_script)
        if not dep_script_path.exists():
            err_msg = f"Dependency script does not exist: {dep_script_path}"
            raise FileNotFoundError(err_msg)
        if dep_script_path.suffix != ".py":
            err_msg = f"Dependency script must be a Python script: {dep_script_path}"
            raise ValueError(err_msg)
        dep_script_paths.append(dep_script_path)

    dep_dir_paths: list[Path] = []
    for dep_dir in dep_dirs:
        dep_dir_path = Path(dep_dir)
        if not dep_dir_path.exists():
            err_msg = f"Dependency directory does not exist: {dep_dir_path}"
            raise FileNotFoundError(err_msg)
        if not dep_dir_path.is_dir():
            err_msg = f"Dependency directory must be a directory: {dep_dir_path}"
            raise ValueError(err_msg)
        dep_dir_paths.append(dep_dir_path)

    return (
        input_file,
        config_file,
        output_dir,
        datafile_paths,
        requirements_retval,
        dep_script_paths,
        dep_dir_paths,
        timeout,
        use_site_packages,
        no_venv,
    )


def _parse_json_config(
    config_path: Path,
) -> list[tuple[str, str | None, str | None, str | None, int | None]]:
    config_list = []
    with config_path.open(mode="r", encoding="utf-8") as f:
        config: dict[str, dict[str, dict[str, str]]] = json.load(f)
        machines_config: dict[str, dict[str, str]] = config["machines"]
    for machine_name, machine_data in machines_config.items():
        host = machine_data.get("hostname")
        user = machine_data.get("username")
        password = machine_data.get("password")
        try:
            md_port = machine_data.get("port")
            port = int(md_port) if md_port else None
        except ValueError as err:
            err_msg = f"Invalid port number for machine: {machine_name}"
            raise ValueError(err_msg) from err
        config_list.append((machine_name, host, user, password, port))
    return config_list


def _parse_cfg_config(
    config_path: Path,
) -> list[tuple[str, str | None, str | None, str | None, int | None]]:
    config_list = []
    config: configparser.ConfigParser = configparser.ConfigParser()
    config.read(config_path)
    for section in config.sections():
        machine_name = section
        host = config[section].get("hostname")
        user = config[section].get("username")
        password = config[section].get("password")
        try:
            port = (
                int(config[section].get("port"))
                if config[section].get("port")
                else None
            )
        except ValueError as err:
            err_msg = f"Invalid port number for machine: {machine_name}"
            raise ValueError(err_msg) from err
        config_list.append((machine_name, host, user, password, port))
    return config_list


def parse_config(config_path: Path) -> list[tuple[str, str, str, str, int | None]]:
    """
    Parse the configuration file.

    Parameters
    ----------
    config_path : Path
        The path to the configuration file.
        A configuration file can be either a json or cfg/ini file.

    Returns
    -------
    list[tuple[str, str, str, str, int | None]]
        A list of tuples containing the machine name, host,
          user, password, and port for each machine.

    Raises
    ------
    ValueError
        If the configuration file is not a json or cfg/ini file.

    """
    config_list = []
    if config_path.suffix == ".json":
        config_list = _parse_json_config(config_path)
    elif config_path.suffix in [".cfg", ".ini"]:
        config_list = _parse_cfg_config(config_path)
    else:
        err_msg = f"Invalid config file type: {config_path}"
        raise ValueError(err_msg)

    # perform some validation
    max_port = 65535
    for machine_name, host, user, password, port in config_list:
        if host is None:
            err_msg = f"Missing hostname for machine: {machine_name}"
            raise ValueError(err_msg)
        if user is None:
            err_msg = f"Missing username for machine: {machine_name}"
            raise ValueError(err_msg)
        if password is None:
            err_msg = f"Missing password for machine: {machine_name}"
            raise ValueError(err_msg)
        if port is not None and not 0 < port < max_port:
            err_msg = f"Invalid port number for machine: {machine_name}"
            raise ValueError(err_msg)

    # for-loop above verifies that the str items are not None
    return config_list  # type: ignore[return-value]
