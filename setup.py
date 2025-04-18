from setuptools import setup, find_packages

setup(
    name='dynamo-utils',
    version='0.4.7',
    description='Python utils for DynamoDB',
    url='',
    author='Kit G.',
    packages=find_packages(
        exclude=[
            "tests.*",
            "tests",
            "*egg*",
            "*pytest*",
            "*.dist-info",
        ]
    ),
)
