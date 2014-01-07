#!/usr/bin/env python
# -*- encodig: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='blackbird-ldap',
    version='0.1.1',
    description='Blackbird plugin for monitoring slapd runtime information.',
    author='Vagrants',
    author_email='vagrants.git@gmail.com',
    url='https://github.com/Vagrants/blackbird-ldap',
    data_files=[
        ('/opt/blackbird/plugins', ['ldap.py'])
    ],
    install_requires=[
        'blackbird>=0.3.2',
        'python-ldap',
    ],
    dependency_links=[
        'https://github.com/Vagrants/blackbird'
        '/tarball/master#egg=blackbird-0.3.2',
    ],
)
