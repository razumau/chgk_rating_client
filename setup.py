import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as rs:
    requirements = rs.read()

setuptools.setup(
    name="chgk_rating_client",
    version="1.0.2",
    author="Jury Razumau",
    author_email="jurazumau@gmal.com",
    description="Клиент для API rating.chgk.info",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    url="https://github.com/razumau/chgk_rating_client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
