#!/bin/bash

#set -e
docker compose build

echo "\n\nCreating docker volumes\n"

docker volume create osprey-postgres-data
docker volume create osprey-endpoint-data
docker volume create osprey-proxystore-data

echo "\n\nRunning migrations"
docker compose up postgres-database -d

sleep 5 # sleep required otherwise attempts to create db before postgres server is started

docker compose exec -it postgres-database bash -c "psql -U ${DATABASE_USER} -c \"CREATE DATABASE osprey_development;\"; exit;"
docker compose run -it web flask db upgrade
docker compose down

# echo "\n\nSetting up Globus Web"
# docker compose run -it globus login --no-local-server

echo "\n\nSetting up Globus Compute Endpoint"

echo "\nThe Globus Endpoint UUID is : "
docker compose run -it globus-endpoint globus-compute-endpoint start default

# out=`docker compose run -it globus-endpoint globus-compute-endpoint list`
# endpoint_uuid=`echo ${out} | grep -i 'default' | awk '{print $2}'`

# create file due to weird issue when storing into variable. Need to test variable method further
endpoint_out="endpoint.out"
docker compose run -it globus-endpoint globus-compute-endpoint list > ${endpoint_out}
endpoint_uuid=`cat ${endpoint_out} | grep -i 'default' | awk '{print $2}'`

echo "\nThe Globus Flow Functions UUIDs are : "
out=`docker compose run -it globus-endpoint python /app/osprey/worker/lib/globus_flow_helper.py`

flow_download_uuid=`echo ${out} | grep -i 'download' | awk '{print $4}' | tr -d '\r'`
flow_database_uuid=`echo ${out} | grep -i 'database' | awk '{print $9}' | tr -d '\r'`
flow_user_function_uuid=`echo ${out} | grep -i 'user' | awk '{print $NF}' | tr -d '\r'`

echo "${out}"
echo "${endpoint_uuid}"
echo "${flow_download_uuid}"
echo "${flow_database_uuid}"
echo "${flow_user_function_uuid}"

echo "\nThe Globus Search index is":
search_idx=`docker compose run -it web python /app/osprey/server/lib/globus_search.py | tail -n 1`

echo "${search_idx}"

echo "\n\nSetting up Globus Flow Worker"
docker compose run -it web python /app/osprey/server/jobs/timer.py
docker compose run -it web python /app/osprey/server/lib/globus_compute.py

if [[ $(uname -a) == *"Darwin"* ]]
then
    sed -i '' "s/GLOBUS_WORKER_UUID=.*/GLOBUS_WORKER_UUID=${endpoint_uuid}/g" docker-compose.yml
    sed -i '' "s/GLOBUS_FLOW_DOWNLOAD_FUNCTION=.*/GLOBUS_FLOW_DOWNLOAD_FUNCTION=${flow_download_uuid}/g" docker-compose.yml
    sed -i '' "s/GLOBUS_FLOW_COMMIT_FUNCTION=.*/GLOBUS_FLOW_COMMIT_FUNCTION=${flow_database_uuid}/g" docker-compose.yml
    sed -i '' "s/GLOBUS_FLOW_USER_COMMIT_FUNCTION=.*/GLOBUS_FLOW_USER_COMMIT_FUNCTION=${flow_user_function_uuid}/g" docker-compose.yml
else
    sed -i "s/GLOBUS_WORKER_UUID=.*/GLOBUS_WORKER_UUID=${endpoint_uuid}/g" docker-compose.yml
    sed -i "s/GLOBUS_FLOW_DOWNLOAD_FUNCTION=.*/GLOBUS_FLOW_DOWNLOAD_FUNCTION=${flow_download_uuid}/g" docker-compose.yml
    sed -i "s/GLOBUS_FLOW_COMMIT_FUNCTION=.*/GLOBUS_FLOW_COMMIT_FUNCTION=${flow_database_uuid}/g" docker-compose.yml
    sed -i "s/GLOBUS_FLOW_USER_COMMIT_FUNCTION=.*/GLOBUS_FLOW_USER_COMMIT_FUNCTION=${flow_user_function_uuid}/g" docker-compose.yml
fi

echo "\n\nUpdated docker-compose.yml"
