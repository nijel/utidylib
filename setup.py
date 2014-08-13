#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup file for easy installation"""

from setuptools import setup


setup(
    packages=['tidy', ],
    package_data={'tidy': ['test_data/*.html']},
    data_files=[],
    name='uTidylib',
    version='0.3',
    author='Michal Čihař',
    author_email='michal@cihar.com',
    url='https://nijel.github.io/utidylib/',
    license='MIT',
    description='Wrapper for HTML Tidy at http://tidy.sourceforge.net',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    long_description='''\
A wrapper for the relocatable version of HTML Tidy (see
http://tidy.sourceforge.net for details).  This allows you to
tidy HTML files through a Pythonic interface.'''
)
