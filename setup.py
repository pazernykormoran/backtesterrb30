from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

requirements = []
with codecs.open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fh:
    req = fh.readline().split("==")[0]
    while req:
        if req  and req != '':
            if req[0:4] == 'git+':
                req = 'xnt-http-api @ ' + req
            requirements.append(req)
        req = fh.readline().split("==")[0]

VERSION = '0.0.1'
DESCRIPTION = 'Stock backtest library'
LONG_DESCRIPTION = 'backtesterRB30 is a framework to backtest your market strategies.'

# Setting up
setup(
    name="backtesterRB30",
    version=VERSION,
    author="Andrzej Daniel",
    author_email="<andrzolide@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    data_files=['backtesterRB30/temporary_ducascopy_list.json'],
    install_requires=requirements,
    keywords=['backtest'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
    ]
)