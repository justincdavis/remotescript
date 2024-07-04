# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
from __future__ import annotations

import argparse
import configparser
import json
import logging
import time
import re
from pathlib import Path

from stdlib_list import stdlib_list

_log = logging.getLogger(__name__)


def parse_and_trim_imports(file_path: Path) -> list[tuple[str, str]]:
    """
    Parse the file for imports and trim empty entries.

    Generates a list of import statements from the file.
    These imports are represented as tuples of two strings.
    The first string is populated if the import statement was in the form:
    from <module> import <name>

    Parameters
    ----------
    file_path : Path
        The path to the file to parse.

    Returns
    -------
    list[tuple[str, str]]
        A list of import statements.

    """
    # Read the file and find import statements using regular expressions
    matches: list[list[tuple[str, str]]] = [
        re.findall(
            r"(?m)^(?:from[ ]+(\S+)[ ]+)?import[ ]+(\S+)(?:[ ]+as[ ]+\S+)?[ ]*$",
            line,
        )
        for line in file_path.open("r").readlines()
    ]

    # Trim empty entries from the list
    num_matches = len(matches)
    for i in range(num_matches - 1, -1, -1):
        if not matches[i]:
            matches.pop(i)

    unnested: list[tuple[str, str]] = []
    for match in matches:
        unnested.extend(match)

    return unnested


def compare_and_prune_libs(libs: list[tuple[str, str]]) -> list[str]:
    """
    Compare libraries to the standard libraries and remove any matches.

    Parameters
    ----------
    libs : list[tuple[str, str]]
        A list of libraries to compare.
    
    Returns
    -------
    list[str]
        A list of libraries with standard libraries removed.

    """
    stdlibs = stdlib_list()
    valid_libs = []
    for lib in libs:
        if lib[0] == "":
            if lib[1] not in stdlibs:
                valid_libs.append(lib)
        else:
            if lib[0] not in stdlibs:
                valid_libs.append(lib)
    cleaned_libs = []
    for vlib in valid_libs:
        if vlib[0] == "":
            cleaned_libs.append(vlib[1])
        else:
            cleaned_libs.append(vlib[0])
    return cleaned_libs


def generate_requirements(libs: list[str]) -> str:
    """
    Generate a requirements file from the list of libraries.

    Parameters
    ----------
    libs : list[str]
        A list of libraries to include in the requirements file.

    Returns
    -------
    str
        The requirements file as a string.

    """
    reqs = ""
    for lib in libs:
        reqs += f"{lib}\n"
    return reqs
