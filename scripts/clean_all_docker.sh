#!/bin/bash

# clean search idx
search_ids=(`docker compose run -it --rm web globus search index list | tail -n +3 | awk '{print $1}'`)
for sidx in "${search_ids[@]}"; do docker compose run -it --rm web globus search index delete $sidx; done

# clean up timers
timer_ids=(`docker compose run -it --rm web globus timer list | grep -i 'timer id' | awk '{print $NF}'`)
for tidx in "${timer_ids[@]}"; do docker compose run -it --rm web globus timer delete $tidx; done

# # clean search idx
# search_ids=(`globus search index list | tail -n +3 | awk '{print $1}'`)
# for sidx in "${search_ids[@]}"; do globus search index delete $sidx; done

# # clean up timers
# timer_ids=(`globus timer list | grep -i 'job id' | awk '{print $NF}'`)
# for tidx in "${timer_ids[@]}"; do globus timer delete $tidx; done

docker compose down
# docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
docker rmi dsaas-web postgres:15.3
