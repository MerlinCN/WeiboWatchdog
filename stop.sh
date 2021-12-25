pid=$(ps -ef |grep "Src/main.py" |head -n1  | awk -F ' ' '{print $2}')
kill -9 $pid