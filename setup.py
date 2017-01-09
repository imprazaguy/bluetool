#!/usr/bin/env python
from distutils.spawn import find_executable
import subprocess

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages


class ProgramNotFoundError(Exception):
    def __init__(self, progname):
        self.progname = progname

    def __str__(self):
        return 'Faild to find program: {}'.format(self.progname)


def find_program(prog, required=None):
    exe_path = find_executable(prog)
    if required and not exe_path:
        raise ProgramNotFoundError(prog)
    return exe_path

PKG_CONFIG = find_program('pkg-config', True)


def pkg_config(pkg):
    return subprocess.check_output(
        [PKG_CONFIG, '--cflags', '--libs', pkg]).split()


def map_flags2dict(*args):
    name_map = {
        '-D': 'define_macros',
        '-I': 'include_dirs',
        '-L': 'library_dirs',
        '-l': 'libraries'
    }
    flag_dict = {}

    def set_flag_dict(flag):
        flag_type = flag[:2]
        if flag_type in name_map:
            flag_dict.setdefault(name_map[flag_type], []).append(flag[2:])
        else:
            flag_dict.setdefault('extra_link_args', []).append(flag)

    for flags in args:
        try:
            for flag in flags:
                set_flag_dict(flag)
        except TypeError:
            set_flag_dict(flags)

    for k, v in flag_dict.iteritems():
        flag_dict[k] = list(set(v))
    return flag_dict


bluez_flags = pkg_config('bluez')

setup(
    name='bluetool',
    version='0.1',
    author='Kuan-Chung Huang',
    author_email='imprazaguy@gmail.com',
    description='Bluetooth Test Tool',
    license='MIT',
    keywords='bluetooth',

    scripts=[
        'scripts/bluetest'
    ],

    install_requires=[
        'PyBluez>=0.18'
    ],
    packages=find_packages()
)
