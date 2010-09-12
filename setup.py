from setuptools import setup, find_packages
import os

f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = f.read()
f.close()

setup(
    name='django-mediasync',
    version="1.0.1",
    description='Django static media development and distribution tools',
    long_description=readme,
    author='Jeremy Carbaugh',
    author_email='jcarbaugh@sunlightfoundation.com',
    url='http://github.com/sunlightlabs/django-mediasync/',
    packages=find_packages(),
    package_data = {
        'mediasync': [
            'tests/media/*',
        ]
    },
    license='BSD License',
    platforms=["any"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Environment :: Web Environment',
    ],
)