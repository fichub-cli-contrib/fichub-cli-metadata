from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='fichub-cli-metadata',
    author='Arbaaz Laskar',
    author_email="arzkar.dev@gmail.com",
    description="A metadata plugin for fetching Metadata from the Fichub API for the fichub-cli",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version='0.4.0',
    license='Apache License',
    url="https://github.com/fichub-cli-contrib/fichub-cli-metadata",
    packages=find_packages(
        include=['fichub_cli_metadata', 'fichub_cli_metadata.*']),
    include_package_data=True,
    install_requires=[
        'fichub-cli>=0.7.0',
        'rich>=10.4.0',
        'sqlalchemy>=1.4.31'
    ],
    entry_points='''
        [console_scripts]
        fichub_cli_metadata=fichub_cli_metadata.cli:app
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
