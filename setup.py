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
    'pydantic',
    'python-binance',
    'pandas',
    'matplotlib',
    'python-dotenv',
    'keyboard',
    'pycoingecko',
    'websocket-client',
    'requests'
]
# with codecs.open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fh:
#     req = fh.readline().split("==")[0]
#     while req:
#         if req  and req != '':
#             requirements.append(req)
#         req = fh.readline().split("==")[0]

DESCRIPTION = 'Stock backtest library'
LONG_DESCRIPTION = 'backtesterRB30 is a framework to backtest your market strategies.'

# Setting up
setup(
    name="backtesterRB30",
    version=cf_remote_version,
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