#!/bin/bash

# TODO: Make sure to change how to check if service is alive to 
# docker compose exec web ........ Eg. Check if echo works or raises error


endpoint_docker=$(docker ps -aq --filter status=running --filter name=osprey-globus-endpoint)
if [ -z "$endpoint_docker" ]
then
    echo "Endpoint Docker is not running"
    return 0
fi

server_docker=$(docker ps -aq --filter status=running --filter name=osprey-web)
if [ -z "$server_docker" ]
then
    echo "Web server is not running"
    return 0
fi

endpoint_id=$(docker exec -it $endpoint_docker globus-compute-endpoint list | grep default | awk '{print $2}')
if [ -z "$endpoint_id" ]
then
    echo "Endpoint is not running on docker"
    return 0
fi

docker compose exec -it web python /app/osprey/server/jobs/timer.py $endpoint_id