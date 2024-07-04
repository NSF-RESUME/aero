#!/bin/bash

#set -e
docker compose build

echo "\n\nCreating docker volumes\n"

docker volume create osprey-postgres-data

echo "\n\nRunning migrations"
docker compose up postgres-database -d

sleep 5 # sleep required otherwise attempts to create db before postgres server is started

# docker compose exec -it postgres-database bash -c "psql -U ${DATABASE_USER} -c \"CREATE DATABASE osprey_development;\"; exit;"
docker compose run -it --rm web flask db upgrade
docker compose down

echo "\nThe Globus Flow Functions UUIDs are : "
docker compose run -it --rm web python /app/osprey/worker/lib/globus_flow_helper.py
source osprey/server/set_flow_uuids.sh

echo "\nThe Globus Search index is":
search_idx=`docker compose run -it --rm web python /app/osprey/server/lib/globus_search.py | head -n 1 | awk '{print $NF}' | tr -d '\r'`

echo "${search_idx}"

echo "\n\nSetting up Globus Flow Worker"
docker compose run -it --rm web python /app/osprey/server/jobs/timer.py
docker compose run -it --rm web python /app/osprey/server/lib/globus_compute.py

if [[ $(uname -a) == *"Darwin"* ]]
then
    sed -i '' "s/GLOBUS_FLOW_DOWNLOAD_FUNCTION=.*/GLOBUS_FLOW_DOWNLOAD_FUNCTION=${FLOW_DOWNLOAD}/g" docker-compose.yml
    sed -i '' "s/GLOBUS_FLOW_COMMIT_FUNCTION=.*/GLOBUS_FLOW_COMMIT_FUNCTION=${FLOW_DB_COMMIT}/g" docker-compose.yml
    sed -i '' "s/GLOBUS_FLOW_USER_COMMIT_FUNCTION=.*/GLOBUS_FLOW_USER_COMMIT_FUNCTION=${FLOW_USER_COMMIT}/g" docker-compose.yml
    sed -i '' "s/SEARCH_INDEX=.*/SEARCH_INDEX=${search_idx}/g" docker-compose.yml
else
    sed -i "s/GLOBUS_FLOW_DOWNLOAD_FUNCTION=.*/GLOBUS_FLOW_DOWNLOAD_FUNCTION=${FLOW_DOWNLOAD}/g" docker-compose.yml
    sed -i "s/GLOBUS_FLOW_COMMIT_FUNCTION=.*/GLOBUS_FLOW_COMMIT_FUNCTION=${FLOW_DB_COMMIT}/g" docker-compose.yml
    sed -i "s/GLOBUS_FLOW_USER_COMMIT_FUNCTION=.*/GLOBUS_FLOW_USER_COMMIT_FUNCTION=${FLOW_USER_COMMIT}/g" docker-compose.yml
    sed -i "s/SEARCH_INDEX=.*/SEARCH_INDEX=${search_idx}/g" docker-compose.yml
fi

echo "\n\nUpdated docker-compose.yml"
