.. _installation:

Installation
------------

There are multiple methods for installing remoterunner. The recommended method is
to install remoterunner into a virtual environment. This will ensure that the
remoterunner dependencies are isolated from other Python projects you may be
working on.

Methods
^^^^^^^
#. Pip:

   .. code-block:: console

      $ pip3 install remoterunner

#. From source:

   .. code-block:: console

      $ git clone https://github.com/justincdavis/remoterunner.git
      $ cd remoterunner
      $ pip3 install .

Optional Dependencies
^^^^^^^^^^^^^^^^^^^^^

#. dev:

   .. code-block:: console

      $ pip3 install remoterunner[dev]
   
   This will install dependencies allowing a full development environment.
   All CI and tools used for development will be installed and can be run.
