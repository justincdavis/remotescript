# Copyright (c) 2024 Justin Davis (davisjustin302@gmail.com)
#
# MIT License
import remoterunner


def test_namespace():
    assert remoterunner.check_bash is not None
    assert remoterunner.run_script is not None
