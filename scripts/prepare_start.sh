#!/bin/bash

#set -e
sudo docker compose build

echo $'\n\nCreating docker volumes\n'

sudo docker volume create osprey-postgres-data

echo $'\n\nRunning migrations'
sudo docker compose up database -d
sleep 5 # sleep required otherwise attempts to create db before postgres server is started

sudo docker compose exec -it -e POSTGRES_PASSWORD=${DATABASE_PASSWORD} database psql -U ${DATABASE_USER} -d ${DATABASE_NAME} -c "\l"
# echo "\nThe Globus Search index is":
# search_idx=`docker compose run -it --rm web python /app/aero/globus/search.py | head -n 1 | awk '{print $NF}' | tr -d '\r'`

# echo "${search_idx}"
