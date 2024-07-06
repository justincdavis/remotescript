# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
from __future__ import annotations

import argparse
import socket
from pathlib import Path

import paramiko

from remoterunner._utils import parse_config


def main() -> None:
    """Delete the run directories on the remote machines."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        help="The configuration file to use for the remote machines.",
        type=str,
        required=True,
    )
    args = parser.parse_args()
    config = args.config
    config_path = Path(config)
    if not config_path.exists():
        print("Configuration file does not exist.")
        return
    if not config_path.is_file():
        print("Configuration file is not a file.")
        return

    for (machine_name, hostname, user, password, port) in parse_config(config_path):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=hostname,
                username=user,
                password=password,
                port=port if port is not None else 22,
                timeout=5,
            )
        except (socket.timeout, OSError):
            print(f"Error connecting to remote machine: {machine_name}")
            continue
        
        client.exec_command("rm -rf runs")

if __name__ == "__main__":
    main()
