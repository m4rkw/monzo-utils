#!/usr/bin/env python

from setuptools import setup

setup(name='monzo-utils',
    version='0.0.96',
    description='Monzo Utils',
    author='Mark Wadham',
    url='https://github.com/m4rkw/monzo-utils',
    packages=['.','monzo_utils/lib','monzo_utils/lib/db_driver','monzo_utils/model'],
    setup_requires=['wheel'],
    scripts=[
        'monzo-sync',
        'monzo-status',
        'monzo-search',
        'monzo-payments'
    ],
    install_requires=[
        'mysqlclient==2.1.1',
        'monzo-api',
        'requests',
        'python-pushover2==0.5',
        'dateparser',
        'PyYAML',
        'govuk-bank-holidays',
        'currencyconverter',
        'freezegun'
    ]
)
