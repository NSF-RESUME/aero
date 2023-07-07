#!/bin/bash

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

docker exec -it $server_docker python /app/osprey/server/jobs/timer/timer.py $endpoint_id