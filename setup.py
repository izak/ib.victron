from setuptools import setup, find_packages

setup(
    name='ib.victron',
    version='0.1',
    description="Python library for communicating with Victron inverters",
    long_description=open("README.md").read(),
    classifiers=[
        "Programming Language :: Python",
        ],
    keywords='python victron mk2',
    author='Izak Burger',
    author_email='isburger@gmail.com',
    url='https://github.com/izak/ib.victron',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['ib'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'pyserial',
    ],
    entry_points="""
        [console_scripts]
        monitor = ib.victron.scripts.monitor:main
        getstate = ib.victron.scripts.getstate:main
        getlimit = ib.victron.scripts.getlimit:main
        setlimit = ib.victron.scripts.setlimit:main
    """,
)
