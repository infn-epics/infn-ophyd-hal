from setuptools import setup, find_packages

__version__ = "2.12.4"

setup(
    name="infn_ophyd_hal",
    version=__version__,
    description="Ophyd HAL for controlling motors, cameras, magnets... specifically INFN facilities",
    author="Andrea Michelotti", 
    author_email="andrea.michelotti@infn.it", 
    # url="https://baltig.infn.it/infn-epics/infn_ophyd_hal", 
    packages=find_packages(),
    install_requires=[
        "ophyd",
        "asyncio",
        "pyepics",
        "pyyaml"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8.3',
)