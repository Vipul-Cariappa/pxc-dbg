# ???: use pyproject.toml instead

from setuptools import setup, Extension

module = Extension("pxc_extension", sources=["pxc.c"])

setup(
    name="pxc_extension",
    version="0.0.1dev",  # ???: not sure how to version this now
    description="Python C Extension Helper Module for pxc",
    ext_modules=[module],
)
