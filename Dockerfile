FROM openstax/selenium-chrome
USER root
ENV TZ="Asia/Shanghai"
WORKDIR /app

COPY . .

RUN  pip3 install -r requirements.txt

RUN git clone https://github.com/MerlinCN/WeiboBot

RUN python3 WeiboBot/setup.py install

RUN  sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN  apt-get clean

RUN  apt-get update && apt-get -y install ttf-wqy-zenhei

ENTRYPOINT [ "python3","WeiboWatchdog/main.py" ]