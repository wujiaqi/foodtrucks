# Foodtrucks
Dockerized foodtruck app that runs on Raspberry Pi. Based on resin/rpi-raspbian base image. 

## How to build and run
Make sure you have Docker installed

###Clone this repo
```sh
$ git clone https://github.com/wujiaqi/foodtrucks.git
```
###Set access tokens in env
Set access tokens and keys for Twitter and Pushbullet in the env.list file
```sh
$ cat env.list
# Twitter access key/tokens
TW_CONSUMER_KEY=<key>
TW_CONSUMER_SECRET=<secret>
TW_ACCESS_TOKEN=<token>
TW_ACCESS_TOKENSECRET=<tokensecret>

# access token for pushbullet
PUSHBULLET_TOKEN=<access token>
```
###docker build
```sh
$ docker build -t rpi-foodtrucks .
```
###Run
```sh
$ docker run -d --name="rpi_foodtrucks" rpi-foodtrucks 
```

