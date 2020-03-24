#!/usr/bin/env python3

from setuptools import setup

setup(name='ocrbenchmark',
      version='1.0',
      description='Python Utilities for ocr benchmark',
      author='Berend Weel',
      author_email='b.weel@esciencecenter.nl',
      packages=['ocrbenchmark.evaluation'],
      scripts=['ocrbenchmark/evaluation/evaluate-single.py', 'ocrbenchmark/evaluation/ocrevaluation_extract.py'])
