.. _installation:

Installation
------------

There are multiple methods for installing remotescript. The recommended method is
to install remotescript into a virtual environment. This will ensure that the
remotescript dependencies are isolated from other Python projects you may be
working on.

Methods
^^^^^^^
#. Pip:

   .. code-block:: console

      $ pip3 install remotescript

#. From source:

   .. code-block:: console

      $ git clone https://github.com/justincdavis/remotescript.git
      $ cd remotescript
      $ pip3 install .

Optional Dependencies
^^^^^^^^^^^^^^^^^^^^^

#. dev:

   .. code-block:: console

      $ pip3 install remotescript[dev]
   
   This will install dependencies allowing a full development environment.
   All CI and tools used for development will be installed and can be run.
