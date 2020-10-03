#!/usr/bin/env python3
# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import os.path
import setuptools

here = os.path.abspath(os.path.dirname(__file__))

metadata = {}
with open(os.path.join(here, 'fitdecode', '__version__.py'),
          mode='r', encoding='utf-8') as f:
    exec(f.read(), metadata)

with open(os.path.join(here, 'README.rst'), mode='r', encoding='utf-8') as f:
    readme = f.read()

with open(os.path.join(here, 'HISTORY.rst'), mode='r', encoding='utf-8') as f:
    history = f.read()

setuptools.setup(
    name=metadata['__title__'],
    version=metadata['__version__'],
    description=metadata['__description__'],
    long_description=readme + '\n\n' + history,
    # long_description_content_type='text/x-rst; charset=UTF-8',
    author=metadata['__author__'],
    author_email=metadata['__author_email__'],
    url=metadata['__url__'],
    license=metadata['__license__'],
    keywords=metadata['__keywords__'],

    # https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6'],

    python_requires='>=3.6',
    zip_safe=False,

    packages=['fitdecode'],
    package_dir={},
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'fitjson=fitdecode.cmd.fitjson:main',
            'fittxt=fitdecode.cmd.fittxt:main']},

    install_requires=[],
    extras_require={'docs': ['sphinx', 'sphinx_rtd_theme']},

    test_suite="tests",
    tests_require=[])
