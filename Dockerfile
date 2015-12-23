FROM resin/rpi-raspbian
MAINTAINER Jiaqi Wu <wooqiaoqi@gmail.com>
LABEL description="Dockerized foodtruck app"
RUN apt-get update && \
    apt-get install -y python python-pip && \
    pip install tweepy \
    apt-get install mongodb \
    service mongodb start
COPY stream_foodtruck.py foodtrucks.cfg /usr/local/bin/
CMD ["python","/usr/local/bin/stream_foodtruck.py"]

