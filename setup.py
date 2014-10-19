#!/usr/bin/env python
from distutils.spawn import find_executable
import os
import sys

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages, Extension

PKG_CONFIG = find_executable('pkg-config')
if not PKG_CONFIG:
    print >>sys.stderr, 'cannot find pkg-config'
    sys.exit(1)

def pkg_config(pkg, **kwargs):
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    for token in commands.getoutput("pkg-config --libs --cflags %s" % ' '.join(packages)).split():
        flag_type = token[:2]
        if flag_map.has_key(flag_type):
            kwargs.setdefault(flag_map.get(flag_type), []).append(token[2:])
        else:
            kwargs.setdefault('extra_link_args', []).append(token)
    # Remove duplicate
    for k, v in kwargs.iteritems():
        kwargs[k] = list(set(v))
    return kwargs

module = Extension('bluez_ext',
        sources=['bluetool/bluez_ext.c'],
        **pkg_config_flags)

setup(name='bluetool',
        version='0.1',
        install_requires=[
            'PyBluez >= 0.18'
            ],

        packages=find_packages(),
        ext_modules=[module],
        
        author='Guan-Zhong Huang',
        author_email='imprazaguy@gmail.com',
        description='Bluetooth Test Tool',
        licencse='MIT',
        keywords='bluetooth'
        )
