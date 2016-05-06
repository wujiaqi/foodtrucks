FROM resin/rpi-raspbian
MAINTAINER Jiaqi Wu <wooqiaoqi@gmail.com>
LABEL description="Dockerized foodtruck app"
RUN apt-get update
RUN apt-get install -y python python-pip && \
    pip install tweepy && \
    pip install pymongo && \
    pip install requests && \
    pip install git+git://github.com/wujiaqi/pushbullet_client.git
RUN apt-get install -y mongodb-server && \
    mkdir -p /data/db
RUN apt-get clean && \
    apt-get purge
COPY ./scripts/start.sh ./stream_foodtruck.py ./foodtrucks.cfg /
RUN chmod 755 start.sh
CMD ["/bin/bash","/start.sh"]

