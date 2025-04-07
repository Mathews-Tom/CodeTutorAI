from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="enlightenai",
    version="0.1.0",
    author="Tom Mathews",
    author_email="tom.mathews@nyu.edu",
    description="An intelligent codebase explainer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mathews-Tom/EnlightenAI",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "enlightenai=enlightenai.cli:main",
        ],
    }
)
