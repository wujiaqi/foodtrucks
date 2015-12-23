FROM resin/rpi-raspbian
MAINTAINER Jiaqi Wu <wooqiaoqi@gmail.com>
LABEL description="Dockerized foodtruck app"
RUN apt-get update && \
    apt-get install -y python python-pip && \
    pip install tweepy && \
    apt-get install -y mongodb && \
    mkdir -p /data/db
COPY ./scripts/start.sh ./stream_foodtruck.py ./foodtrucks.cfg /
RUN chmod 755 start.sh
CMD ["/bin/bash","/start.sh"]

