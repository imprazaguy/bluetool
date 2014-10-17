from setuptools import setup, find_packages, Extension

module = Extension('bluez_ext',
        sources=['bluetool/bluez_ext.c'])

setup(name='bluetool',
        version='0.1',

        packages=find_packages(),
        ext_modules=[module],
        
        author='Guan-Zhong Huang',
        author_email='imprazaguy@gmail.com',
        description='Bluetooth Test Tool',
        licencse='MIT',
        keywords='bluetooth'
        )
