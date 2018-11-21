import os
from setuptools import setup

def get_long_description(path):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    with open(path) as f:
        return f.read()

setup(
    name='ole-py',
    version='0.0.2',
    url='https://github.com/hallazzang/ole-py',
    license='MIT',
    author='Hanjun Kim',
    author_email='hallazzang@gmail.com',
    description='Lightweight Microsoft OLE file parser in pure Python',
    long_description=get_long_description('README.rst'),
    py_modules=['ole','utils'],
    python_requires='>=3',
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
