#!/bin/bash

docker compose build
echo "\n\nCreating docker volumes\n"

docker volume create osprey-postgres-data
docker volume create osprey-endpoint-data
docker volume create osprey-proxystore-data

# echo "\n\nSetting up Globus Web"
# docker compose run -it globus login --no-local-server

echo "\n\nSetting up Globus Compute Endpoint"

echo "\nThe Globus Endpoint UUID is : "
docker compose run -it globus-endpoint globus-compute-endpoint start default

out=`docker compose run -it globus-endpoint globus-compute-endpoint list`
endpoint_uuid=`echo $out | grep -i 'default' | awk '{print $2}'`

echo "\nThe Globus Flow Functions UUIDs are : "
out=`docker compose run -it globus-endpoint python /app/osprey/worker/lib/globus_flow_helper.py`

flow_download_uuid=`echo ${out} | grep -i 'download' | awk '{print $NF}'`
flow_database_uuid=`echo ${out} | grep -i 'database' | awk '{print $NF}'`
flow_user_function_uuid=`echo ${out} | grep -i 'user' | awk '{print $NF}'`

echo "${out}"

echo "\n\nRunning migrations"
docker compose up postgres-database -d
docker compose exec -it postgres-database bash -c "psql -U postgres -c \"CREATE DATABASE osprey_development;\"; exit;"
docker compose run -it web flask db upgrade
docker compose down

echo "\n\nSetting up Globus Flow Worker"
docker compose run -it web python /app/osprey/server/jobs/timer.py
docker compose run -it web python /app/osprey/server/lib/globus_compute.py

# TODO: make MacOS compatible by adding conditional. ...sed -i '' "s.. 
sed -i "s/GLOBUS_WORKER_UUID=.*/GLOBUS_WORKER_UUID=${endpoint_uuid}/g" docker-compose.yml
sed -i "s/GLOBUS_FLOW_DOWNLOAD_FUNCTION=.*/GLOBUS_FLOW_DOWNLOAD_FUNCTION=${flow_download_uuid}/g" docker-compose.yml
sed -i "s/GLOBUS_FLOW_COMMIT_FUNCTION=.*/GLOBUS_FLOW_COMMIT_FUNCTION=${flow_database_uuid}/g" docker-compose.yml
sed -i "s/GLOBUS_FLOW_USER_COMMIT_FUNCTION=.*/GLOBUS_FLOW_USER_COMMIT_FUNCTION=${flow_user_function_uuid}/g" docker-compose.yml

echo "\n\nUpdated docker-compose.yml"