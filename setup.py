import codecs
import os
import pathlib
import re
import sys
from distutils.command.build_ext import build_ext
from distutils.errors import (CCompilerError, DistutilsExecError,
                              DistutilsPlatformError)

from setuptools import Extension, setup


if sys.version_info < (3, 5, 3):
    raise RuntimeError("aiohttp 3.x requires Python 3.5.3+")


NO_EXTENSIONS = bool(os.environ.get('AIOHTTP_NO_EXTENSIONS'))  # type: bool

if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


here = pathlib.Path(__file__).parent


if (here / '.git').exists() and not (here / 'vendor/http-parser/README.md'):
    print("Install submodules when building from git clone", file=sys.stderr)
    print("Hint:", file=sys.stderr)
    print("  git submodule update --init", file=sys.stderr)
    sys.exit(2)


# NOTE: makefile cythonizes all Cython modules

extensions = [Extension('aiohttp._websocket', ['aiohttp/_websocket.c']),
              Extension('aiohttp._http_parser',
                        ['aiohttp/_http_parser.c',
                         'vendor/http-parser/http_parser.c',
                         'aiohttp/_find_header.c'],
                        define_macros=[('HTTP_PARSER_STRICT', 0)],
                        ),
              Extension('aiohttp._frozenlist',
                        ['aiohttp/_frozenlist.c']),
              Extension('aiohttp._helpers',
                        ['aiohttp/_helpers.c']),
              Extension('aiohttp._http_writer',
                        ['aiohttp/_http_writer.c'])]


class BuildFailed(Exception):
    pass


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except (DistutilsPlatformError, FileNotFoundError):
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError,
                DistutilsPlatformError, ValueError):
            raise BuildFailed()



txt = (here / 'aiohttp' / '__init__.py').read_text('utf-8')
try:
    version = re.findall(r"^__version__ = '([^']+)'\r?$",
                         txt, re.M)[0]
except IndexError:
    raise RuntimeError('Unable to determine version.')

install_requires = [
    'attrs>=17.3.0',
    'chardet>=2.0,<4.0',
    'multidict>=4.0,<5.0',
    'async_timeout>=3.0,<4.0',
    'yarl>=1.0,<2.0',
    'idna-ssl>=1.0; python_version<"3.7"',
    'typing_extensions>=3.6.5',
]


def read(f):
    return (here / f).read_text('utf-8').strip()


args = dict(
    name='aiohttp',
    version=version,
    description='Async http client/server framework (asyncio)',
    long_description='\n\n'.join((read('README.rst'), read('CHANGES.rst'))),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: AsyncIO',
    ],
    author='Nikolay Kim',
    author_email='fafhrd91@gmail.com',
    maintainer=', '.join(('Nikolay Kim <fafhrd91@gmail.com>',
                          'Andrew Svetlov <andrew.svetlov@gmail.com>')),
    maintainer_email='aio-libs@googlegroups.com',
    url='https://github.com/aio-libs/aiohttp',
    project_urls={
        'Chat: Gitter': 'https://gitter.im/aio-libs/Lobby',
        'CI: AppVeyor': 'https://ci.appveyor.com/project/aio-libs/aiohttp',
        'CI: Circle': 'https://circleci.com/gh/aio-libs/aiohttp',
        'CI: Shippable': 'https://app.shippable.com/github/aio-libs/aiohttp',
        'CI: Travis': 'https://travis-ci.com/aio-libs/aiohttp',
        'Coverage: codecov': 'https://codecov.io/github/aio-libs/aiohttp',
        'Docs: RTD': 'https://docs.aiohttp.org',
        'GitHub: issues': 'https://github.com/aio-libs/aiohttp/issues',
        'GitHub: repo': 'https://github.com/aio-libs/aiohttp',
    },
    license='Apache 2',
    packages=['aiohttp'],
    python_requires='>=3.5.3',
    install_requires=install_requires,
    extras_require={
        'speedups': [
            'aiodns',
            'Brotli',
            'cchardet',
        ],
    },
    include_package_data=True,
)

if not NO_EXTENSIONS:
    print("**********************")
    print("* Accellerated build *")
    print("**********************")
    setup(ext_modules=extensions,
          cmdclass=dict(build_ext=ve_build_ext),
          **args)
else:
    print("*********************")
    print("* Pure Python build *")
    print("*********************")
    setup(**args)
