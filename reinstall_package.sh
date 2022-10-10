python3 setup.py sdist bdist_wheel
cd dist
sudo pip3 uninstall -y backtesterRB30
sudo pip3 install backtesterRB30-v0.1.0-1-g05c3cae.tar.gz