#!/usr/bin/env python

from setuptools import setup

setup(name='monzo-utils',
    version='0.0.6',
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
        'python-pushover2==0.5',
        'dateparser'
    ]
)
