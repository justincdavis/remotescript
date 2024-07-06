# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
import remotescript


def test_namespace():
    assert remotescript.check_bash is not None
    assert remotescript.run_script is not None
