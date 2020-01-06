from setuptools import setup


setup(
    name="qmc0dec",
    version="0.0.1",
    author="Nift1C4t",
    author_email="nift1c4t@gmail.com",
    description = "Decodes qmc encoded files",
    packages=["qmc0dec"],
    install_requires = [
        "Click==7.0",
        "tqdm"
    ],
    entry_points='''
        [console_scripts]
        qmc0dec=qmc0dec.decode:cli
    ''',
    keywords = "qmc0 qmc3 qmcogg qmcflac",
    license = "MIT",
    url = "https://github.com/nift1c4t/qmc0dec",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ]
)


