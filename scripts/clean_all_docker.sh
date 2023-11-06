#!/bin/bash

docker-compose down
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
docker rmi dsaas-web dsaas-globus-endpoint postgres:15.3
