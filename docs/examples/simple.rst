.. _examples_simple:

Example: simple.py
==================

.. code-block:: python

	# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
	#
	# MIT License
	"""Basic example showcasing hardware information and NumPy version."""
	
	from __future__ import annotations
	
	import platform
	from platform import system_alias
	
	import numpy as np
	
	if __name__ == "__main__":
	    print(platform.system())
	    print(system_alias(platform.system(), platform.release(), platform.version()))
	    print(platform.release())
	    print(f"NumPy Version: {np.__version__}")

