# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
# ruff: noqa: S507, PERF203
from __future__ import annotations

import socket
import logging
import time
import json
from typing import TYPE_CHECKING

import paramiko
import scp

if TYPE_CHECKING:
    from pathlib import Path

_log = logging.getLogger(__name__)


def run_script(
    machine_name: str,
    hostname: str,
    user: str,
    password: str,
    port: int | None,
    script_path: Path,
    output_dir_path: Path,
    deps: Path,
    datafiles: list[Path] | None = None,
    dep_scripts: list[Path] | None = None,
    timeout: int = 5,
) -> None:
    """
    Run the script on the remote machine.

    Parameters
    ----------
    machine_name : str
        The name of the machine.
    hostname : str
        The hostname of the machine.
    user : str
        The user to connect as.
    password : str
        The password to connect with.
    port : int
        The port to connect on.
    script_path : Path
        The path to the script to run.
    output_dir_path : Path
        The path to the output directory.
    datafiles : list[Path]
        The data files to transfer.
    deps : Path | None
        The dependencies to install.
    dep_scripts : list[Path] | None
        The dependency scripts to run.
    timeout : int
        The timeout for the connection.

    """
    _log.debug(f"{machine_name}: Starting run_script")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=hostname,
            username=user,
            password=password,
            port=port if port is not None else 22,
            timeout=timeout,
        )
    except socket.timeout:
        _log.error(f"{machine_name}: Connection timed out, exiting.")
        return
    except socket.error as er:
        _log.error(f"{machine_name}: Socket error: {er}")
        return
    _log.debug(f"{machine_name}: Connected")

    try:
        client.exec_command("python3 --version")
        _log.debug(f"{machine_name}: Python3 found")
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Python3 not found, exiting.")
        return

    # create new directory for which to run the script and create
    # the virtual environment
    base_directory = "runs"
    run_directory = f"run_{int(time.time())}"
    machine_directory = f"{base_directory}/{run_directory}"
    try:
        client.exec_command(f"mkdir -p {machine_directory}")
        _log.debug(f"{machine_name}: Created directory for execution, {machine_directory}")
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not create virtualenv directory")
        return

    # create the scp_client
    try:
        scp_client = scp.SCPClient(client.get_transport())
        _log.debug(f"{machine_name}: Created SCPClient")
    except scp.SCPException as err:
        _log.error(f"{machine_name}: Could not create SCPClient: {err}")
        return

    # transfer the files
    try:
        scp_client.put(str(script_path), f"{machine_directory}/script.py")
        _log.debug(f"{machine_name}: Transferred {script_path} to {machine_directory}/script.py")
        if datafiles is not None:
            for datafile in datafiles:
                scp_client.put(str(datafile), f"{machine_directory}/{datafile.name}")
                _log.debug(f"{machine_name}: Transferred datafile {datafile} to {machine_directory}/{datafile.name}")
        if deps is not None:
            scp_client.put(str(deps), f"{machine_directory}/requirements.txt")
            _log.debug(f"{machine_name}: Transferred requirements file")
        if dep_scripts is not None:
            for dep_script in dep_scripts:
                scp_client.put(str(dep_script), f"{machine_directory}/{dep_script.name}")
                _log.debug(f"{machine_name}: Transferred dependency script {dep_script}")
        _log.debug(f"{machine_name}: Transferred all files")
    except scp.SCPException as err:
        _log.error(f"{machine_name}: Could not transfer files: {err}")
        return

    # ensure virtualenv is installed
    try:
        client.exec_command("python3 -m pip install virtualenv")
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not install virtualenv")
        return
    
    # create the virtual environment
    try:
        client.exec_command(f"python3 -m venv {machine_directory}/env")
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not create virtualenv")
        return
    
    # install the dependencies
    try:
        command = f"{machine_directory}/env/bin/activate;"
        command += f"python3 -m pip install -r {machine_directory}/requirements.txt;"
        command += "deactivate"
        client.exec_command(command)
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not install dependencies")
        return

    # run the script
    try:
        _, start_time_stdout, _ = client.exec_command("python3 -c 'import time; print(int(time.time()))'")
        command = f"cd {machine_directory};"
        command += "env/bin/activate;"
        command += "python3 script.py;"
        command += "deactivate"
        _, stdout, stderr = client.exec_command(command)
        _, end_time_stdout, _ = client.exec_command("python3 -c 'import time; print(int(time.time()))'")
    
        start_time = int(start_time_stdout.read().decode().strip())
        end_time = int(end_time_stdout.read().decode().strip())
        total_time = end_time - start_time
        _log.debug(f"{machine_name}: Script ran in {total_time} seconds")
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not run script")
        return
    
    # clean the environment
    try:
        client.exec_command(f"rm -rf {machine_directory}/env")
        _log.debug(f"{machine_name}: Cleaned up environment")
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not clean up environment")
        return

    # transfer the run directory into the output directory for the machine
    try:
        scp_client.get(f"{machine_directory}", f"{output_dir_path}/{run_directory}", recursive=True)
        _log.debug(f"{machine_name}: Transferred output directory")
    except scp.SCPException as err:
        _log.error(f"{machine_name}: Could not transfer output directory back to host: {err}")
        return
    
    # write stdout, stderr to files
    stdout_path = output_dir_path / "stdout.txt"
    stderr_path = output_dir_path / "stderr.txt"
    stdout_path.touch(exist_ok=True)
    stderr_path.touch(exist_ok=True)
    stdout_path.write_text(stdout.read().decode())
    stderr_path.write_text(stderr.read().decode())
    _log.debug(f"{machine_name}: Wrote stdout, stderr to files")

    # write output.json
    output_json = {
        "start_time": start_time,
        "end_time": end_time,
        "total_time": total_time,
    }
    output_json_path = output_dir_path / "output.json"
    output_json_path.touch(exist_ok=True)
    with output_json_path.open("w") as f:
        json.dump(output_json, f, indent=4)
