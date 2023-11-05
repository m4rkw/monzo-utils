#!/usr/bin/env python

from setuptools import setup

setup(name='monzo-utils',
    version='0.0.2',
    description='Monzo Utils',
    author='Mark Wadham',
    url='https://github.com/m4rkw/monzo-utils',
    packages=['.'],
    setup_requires=['wheel'],
    scripts=[
        'monzo-sync',
        'monzo-status',
        'monzo-search',
        'monzo-payments'
    ],
    install_requires=[
        'mysqlclient',
        'monzo-api',
        'requests',
        'setuptools==58',
        'python-pushover==0.4'
    ]
)
