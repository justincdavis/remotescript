.. _usage:

Usage
------------

remotescript is designed to let you run Python scripts on a remote machine.
It is a simple tool which only requires that Python3 and Bash be installed
the machine yet you would like the scripts to be installed.

Once remotescript connects to the remote machine, it will copy the script
and any dependencies (such as data files, other scripts, etc.) to the machine
and then build a virtual environment for the Python dependencies.

Here is an example in action:

1.  Create a Python script that you would like to run on a remote machine.
    For example, let's create a script called ``info.py`` which reads some
    information from the system and prints it out:

    .. code-block:: python

        import platform
        from platform import system_alias

        if __name__ == "__main__":
            print(platform.system())
            print(system_alias(platform.system(), platform.release(), platform.version()))
            print(platform.release())

2.  Create a dependency file which lists what Python libraries are required
    for execution of that script. For this simple example, since platform is
    a built-in library, we do not need a dependency file. However, when a
    dependency file is not given, remotescript will attempt to build one for
    you by scanning the imports of the primary script. It is recommended that
    a file is provided to avoid any issues.

    In this case our file would simply be an empty file called ``requirements.txt``.

3.  Create a configuration file for which machines we would like the script to
    run on. For example, let's create a file called "config.cfg" with the
    information on 2 different machines:

    .. code-block:: ini

        [machine1]
        host = 192.168.1.33
        user = user1
        password = password1

        [machine2]
        host = 192.168.1.34
        user = user2
        password = password2
        port = 14958

    In this example file, one of the machines has a port specified. If no port
    is specified, the default port of 22 will be used.

3.  Run the script using remotescript:

    .. code-block:: Bash

        $ python3 -m remotescript --script info.py --requirements requirements.txt --config config.cfg --output /output

4.  The output is saved in the directory specified by the ``--output`` flag.
    The output directory will contain subdirectory for each machines name,
    which were given by the section names in the configuration file.

    The directory will look something like the following:

    output_dir/
    --- machine1/
    ------ output.json  # contains high level information about script execution
    ------ stdout  # text file containing the stdout of the script execution
    ------ stderr  # text file containing the stderr of the script execution
    ------ setup_stdout  # text file containing the stdout of the setup process
    ------ setup_stderr  # text file containing the stderr of the setup process
