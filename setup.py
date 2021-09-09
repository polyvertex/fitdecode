#!/usr/bin/env python3
# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import os.path
import setuptools

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

META = {}
with open(
        os.path.join(THIS_DIR, 'fitdecode', '__meta__.py'),
        mode='rt', encoding='utf-8', errors='strict') as fp:
    exec(fp.read(), META)

with open(
        os.path.join(THIS_DIR, 'README.rst'),
        mode='rt', encoding='utf-8', errors='strict') as fp:
    readme = fp.read()

with open(
        os.path.join(THIS_DIR, 'HISTORY.rst'),
        mode='rt', encoding='utf-8', errors='strict') as fp:
    history = fp.read()

setuptools.setup(
    name=META['__title__'],
    version=META['__version__'],
    description=META['__description__'],
    long_description=readme + '\n\n' + history,
    # long_description_content_type='text/x-rst; charset=UTF-8',
    author=META['__author__'],
    author_email=META['__author_email__'],
    url=META['__url__'],
    license=META['__license__'],
    keywords=META['__keywords__'],

    # https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
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
