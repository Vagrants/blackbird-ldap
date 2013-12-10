#!/usr/bin/env python
# -*- encodig: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='blackbird-ldap',
    version='0.1.0',
    description=(
        'Get monitorring stats  of ldap for blackbird '
        'by using ldapsearch.'
    ),
    author='Vagrants',
    author_email='vagrants.git@gmail.com',
    url='https://github.com/Vagrants/blackbird-ldap',
    data_files=[
        ('/opt/blackbird/plugins', ['ldap.py'])
    ]
)
