from setuptools import setup, find_packages
import codecs
import os
import subprocess

here = os.path.abspath(os.path.dirname(__file__))

cf_remote_version = (
    subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
    .stdout.decode("utf-8")
    .strip()
)

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

requirements = [
    'numpy',
    'asyncio',
    'pyzmq',
    'pydantic==1.9.1',
    'python-binance',
    'pandas',
    'matplotlib',
    'python-dotenv',
    'keyboard',
    'pycoingecko==3.1.0',
    'websocket-client',
    'deepdiff>=4.0.5',
    'inflection==0.3.1',
    'requests>=2.22.0',
    'backoff==1.10.0',
    'PyJWT==1.7.1',
    'backoff==2.2.1',
    'appdirs==1.4.4'
]


DESCRIPTION = 'Stock backtest library'
LONG_DESCRIPTION = 'backtesterrb30 is a framework to backtest your market strategies.'

# Setting up
setup(
    name="backtesterrb30",
    version=cf_remote_version,
    author="Andrzej Daniel",
    author_email="<andrzolide@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    data_files=['backtesterrb30/temporary_ducascopy_list.json'],
    install_requires=requirements,
    keywords=['backtest'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
    ]
)