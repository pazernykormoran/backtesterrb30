trap ctrl_c INT

function ctrl_c() {
        echo "** Trapped CTRL-C"
        killall python3 
        exit 2
}

sudo python3 serve.py python_backtester &
sudo python3 serve.py python_engine &
sudo python3 serve.py python_executor &
sudo python3 serve.py historical_data_feeds &

while true
do
    sleep 10
done
