from distutils.core import setup

long_description = open('README.md').read()

setup(
    name='django-mediasync',
    version="1.0.1",
    package_dir={'mediasync': 'mediasync'},
    packages=['mediasync','mediasync.clients','mediasync.management',
              'mediasync.management.commands','mediasync.templatetags',
              'mediasync.utils'],
    description='Django static media development and distribution tools',
    author='Jeremy Carbaugh',
    author_email='jcarbaugh@sunlightfoundation.com',
    license='BSD License',
    url='http://github.com/sunlightlabs/django-mediasync/',
    #long_description=long_description,
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