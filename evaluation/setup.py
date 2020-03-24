#!/usr/bin/env python

from setuptools import setup

setup(name='ocrbenchmark',
      version='1.0',
      description='Python Utilities for ocr benchmark',
      author='Berend Weel',
      author_email='b.weel@esciencecenter.nl',
      packages=['ocrbenchmark.evaluation'],
      install_requires=[
          'click>=7', 'pytest>=5.4', 'untangle>=1.1', 'cwltool>=2',
          'numpy>=1.18', 'Shapely>=1.7', 'beautifulsoup4>=4.8', 'nlppln>=0.3.3'
      ],
      scripts=[
          'ocrbenchmark/evaluation/evaluate_single.py',
          'ocrbenchmark/evaluation/evaluate_all.py',
          'ocrbenchmark/evaluation/ocrevaluation_extract.py'
      ])
