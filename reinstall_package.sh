python3 setup.py sdist bdist_wheel
cd dist
sudo pip3 uninstall -y backtesterRB30-0.0.1-py3-none-any.whl
sudo pip3 install backtesterRB30-0.0.1-py3-none-any.whl