import io
from setuptools import find_packages, setup


def get_requirements():
    with open("requirements.txt", "r") as f:
        requirements = f.read()
    return list(filter(lambda x: x != "", requirements.split()))


main_ns = {}
with open("version.py") as f:
    exec(f.read(), main_ns)

setup(
    name="video_mover",
    version=main_ns["__version__"],
    description="Package for moving and processing video files.",
    author="Jacob Pelster",
    author_email="jtp246@cornell.edu",
    url="https://github.com/jacobpelster/video_mover",
    license="MIT",
    keywords="video processing file management",
    packages=find_packages(),
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    install_requires=get_requirements(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
