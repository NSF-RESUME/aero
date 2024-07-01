#!/bin/bash

docker compose down
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
docker rmi dsaas-web dsaas-globus-endpoint postgres:15.3

# clean search idx
search_ids=(`globus search index list | tail -n +3 | awk '{print $1}'`)
for sidx in "${search_ids[@]}"; do globus search index delete $sidx; done

# clean up timers
timer_ids=(`globus timer list | grep -i 'timer id' | awk '{print $NF}'`)
for tidx in "${timer_ids[@]}"; do globus timer delete $tidx; done

# clean search idx
search_ids=(`globus search index list | tail -n +3 | awk '{print $1}'`)
for sidx in "${search_ids[@]}"; do globus search index delete $sidx; done

# clean up timers
timer_ids=(`globus timer list | grep -i 'job id' | awk '{print $NF}'`)
for tidx in "${timer_ids[@]}"; do globus timer delete $tidx; done
