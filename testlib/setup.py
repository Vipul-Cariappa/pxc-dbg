# ???: use pyproject.toml instead

from setuptools import setup, Extension

module = Extension("pxctest", sources=["pxc-test.c"])

setup(
    name="pxctest",
    version="0.0.1dev",  # ???: not sure how to version this now
    description="Python C Extension Module to test pxc-dbg",
    ext_modules=[module],
)
