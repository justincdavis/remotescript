# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
# ruff: noqa: S507
from __future__ import annotations

import json
import logging
import socket
import time
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
    def write_stdout_stderr(stdout: str, stderr: str):
        """Write the stdout and stderr to files before exit."""
        _log.debug(f"{machine_name}: Exiting")
        # write stdout, stderr to files
        stdout_path = output_dir_path / "stdout.txt"
        stderr_path = output_dir_path / "stderr.txt"
        stdout_path.touch(exist_ok=True)
        stderr_path.touch(exist_ok=True)
        stdout_path.write_text(stdout)
        stderr_path.write_text(stderr)
        _log.debug(f"{machine_name}: Wrote stdout, stderr to files")
        _log.debug(f"{machine_name}: Starting run_script")

    # begin running logs for stdout and stderr of the script
    stdout = ""
    stderr = ""

    # create client and connect
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
        write_stdout_stderr(stdout, stderr)
        return
    except OSError as er:
        _log.error(f"{machine_name}: Socket error: {er}")
        write_stdout_stderr(stdout, stderr)
        return
    _log.debug(f"{machine_name}: Connected")

    # check for python3
    try:
        _, py3_stdout, py3_stderr = client.exec_command("python3 --version")
        _log.debug(f"{machine_name}: Python3 found")
        stdout += py3_stdout.read().decode()
        stderr += py3_stderr.read().decode()
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Python3 not found, exiting.")
        write_stdout_stderr(stdout, stderr)
        return

    # create new directory for which to run the script and create
    # the virtual environment
    base_directory = "runs"
    run_directory = f"run_{int(time.time())}"
    machine_directory = f"{base_directory}/{run_directory}"
    try:
        _, mk_stdoutt, mk_stderr = client.exec_command(f"mkdir -p {machine_directory}")
        _log.debug(
            f"{machine_name}: Created directory for execution, {machine_directory}",
        )
        stdout += mk_stdoutt.read().decode()
        stderr += mk_stderr.read().decode()
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not create virtualenv directory")
        write_stdout_stderr(stdout, stderr)
        return

    # create the scp_client
    try:
        scp_client = scp.SCPClient(client.get_transport())
        _log.debug(f"{machine_name}: Created SCPClient")
    except scp.SCPException as err:
        _log.error(f"{machine_name}: Could not create SCPClient: {err}")
        write_stdout_stderr(stdout, stderr)
        return

    # transfer the files
    try:
        scp_client.put(str(script_path), f"{machine_directory}/script.py")
        _log.debug(
            f"{machine_name}: Transferred {script_path} to {machine_directory}/script.py",
        )
        if datafiles is not None:
            for datafile in datafiles:
                scp_client.put(str(datafile), f"{machine_directory}/{datafile.name}")
                _log.debug(
                    f"{machine_name}: Transferred datafile {datafile} to {machine_directory}/{datafile.name}",
                )
        if deps is not None:
            scp_client.put(str(deps), f"{machine_directory}/requirements.txt")
            _log.debug(f"{machine_name}: Transferred requirements file")
        if dep_scripts is not None:
            for dep_script in dep_scripts:
                scp_client.put(
                    str(dep_script),
                    f"{machine_directory}/{dep_script.name}",
                )
                _log.debug(
                    f"{machine_name}: Transferred dependency script {dep_script}",
                )
        _log.debug(f"{machine_name}: Transferred all files")
    except scp.SCPException as err:
        _log.error(f"{machine_name}: Could not transfer files: {err}")
        write_stdout_stderr(stdout, stderr)
        return

    # ensure virtualenv is installed
    try:
        _, venv_install_stdout, venv_install_stderr = client.exec_command("python3 -m pip install virtualenv")
        stdout += venv_install_stdout.read().decode()
        stderr += venv_install_stderr.read().decode()
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not install virtualenv")
        write_stdout_stderr(stdout, stderr)
        return

    # create the virtual environment
    try:
        _, venv_create_stdout, venv_create_stderr = client.exec_command(f"python3 -m venv {machine_directory}/env")
        stdout += venv_create_stdout.read().decode()
        stderr += venv_create_stderr.read().decode()
        if venv_create_stderr.read().decode():
            _log.error(f"{machine_name}: Could not create virtualenv")
            write_stdout_stderr(stdout, stderr)
            return
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not create virtualenv")
        write_stdout_stderr(stdout, stderr)
        return

    # install the dependencies
    try:
        command = f"source {machine_directory}/env/bin/activate;"
        command += f"python3 -m pip install -r {machine_directory}/requirements.txt;"
        command += "deactivate"
        _, command_stdout, command_stderr = client.exec_command(command)
        env_stdout_text = command_stdout.read().decode()
        env_stderr_text = command_stderr.read().decode()
        stdout += env_stdout_text
        stderr += env_stderr_text

        # evaluate the output of the virtualenv installation
        failed = False
        if not "Successfully installed" in env_stdout_text or "Requirement already satisfied" in env_stdout_text:
            # _log.error(f"{machine_name}: dep install STDOUT: {env_stdout_text}")
            failed = True
        if env_stderr_text:
            _log.error(f"{machine_name}: Error installing the dependencies, attempting run anyways...")
            # _log.error(f"{machine_name}: dep install STDERR: {env_stderr_text}")
            # failed = True
        if failed:
            return
    except paramiko.SSHException:
        _log.error(f"{machine_name}: Could not install dependencies")
        write_stdout_stderr(stdout, stderr)
        return

    # run the script
    try:
        # start time
        # TODO: convert to new stdout/stderr model
        failed_time = False
        _, start_time_stdout, st_stderr = client.exec_command(
            "python3 -c 'import time; print(int(time.time()))'",
        )
        if st_stderr.read().decode():
            failed_time = True

        # actual script run
        command = f"cd {machine_directory};"
        command += "source env/bin/activate;"
        command += "python3 script.py;"
        command += "deactivate"
        _, stdout, stderr = client.exec_command(command)

        # end time
        _, end_time_stdout, et_stderr = client.exec_command(
            "python3 -c 'import time; print(int(time.time()))'",
        )
        if et_stderr.read().decode():
            failed_time = True

        # generate total time or n/a if failed
        if not failed_time:
            start_time = int(start_time_stdout.read().decode().strip())
            end_time = int(end_time_stdout.read().decode().strip())
            total_time = end_time - start_time
        else:
            total_time = "n/a"
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
        scp_client.get(
            f"{machine_directory}",
            f"{output_dir_path}/{run_directory}",
            recursive=True,
        )
        _log.debug(f"{machine_name}: Transferred output directory")
    except scp.SCPException as err:
        _log.error(
            f"{machine_name}: Could not transfer output directory back to host: {err}",
        )
        return

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
