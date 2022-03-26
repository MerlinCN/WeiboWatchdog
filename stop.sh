pid=$(ps -ef |grep "python3 WeiboWatchdog/main.py" |grep -v "grep" |head -n1  | awk -F ' ' '{print $2}')
kill -9 $pid
echo "关闭 $pid 成功"