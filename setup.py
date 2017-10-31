from distutils.core import setup
#from setuptools import setup

setup(
    name='selfstoredict',
    version='0.5',
    packages=['selfstoredict'],
    url='https://github.com/markus61/selfstoredict',
    license='MIT',
    author='markus',
    author_email='ms@dom.de',
    description='a python class delivering a dict that stores itself into a JSON file or a redis db'
)
