python3 setup.py sdist bdist_wheel
cd dist
sudo pip3 uninstall -y backtesterRB30
sudo pip3 install backtesterRB30-v0.1.0_2_g7280697-py3-none-any.whl