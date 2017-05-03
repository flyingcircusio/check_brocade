"""Monitor Brocade VDX 6740 switches through Sensu or Nagios."""

from setuptools import setup, find_packages
import glob


setup(
    name='check_brocade',
    version='0.1',
    install_requires=[
        'PTable',
        'pytz',
        'requests',
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-cache',
            'pytest-capturelog',
            'pytest-codecheckers',
            'pytest-cov',
            'pytest-timeout',
        ],
    },
    entry_points="""
        [console_scripts]
            check_brocade = check_brocade:main

    """,
    author='Christian Theune <ct@flyingcircus.io>',
    author_email='ct@flyingcircus.io',
    license='GPL-3',
    url='https://bitbucket.org/flyingcircus/check_brocade',
    keywords='brocade monitoring sensu nagios',
    classifiers="""\
Environment :: Console
Intended Audience :: System Administrators
License :: OSI Approved :: GNU General Public License v3 (GPLv3)
Operating System :: POSIX
Programming Language :: Python
Programming Language :: Python :: 3
"""[:-1].split('\n'),
    description=__doc__.strip(),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    data_files=[('', glob.glob('*.txt'))],
    zip_safe=False,
    cmdclass={'test': PyTest},
)
