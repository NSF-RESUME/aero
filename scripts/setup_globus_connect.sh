#!/bin/bash

# Installation
curl -LOs https://downloads.globus.org/globus-connect-server/stable/installers/repo/deb/globus-repo_latest_all.deb
sudo dpkg -i globus-repo_latest_all.deb
sudo apt-key add /usr/share/globus-repo/RPM-GPG-KEY-Globus
sudo apt update
sudo apt install globus-connect-server54


# Setup
sudo globus-connect-server endpoint setup "Osprey GCS Staging" \
    --organization “OspreyDev” \
    --owner sudershan@uchicago.edu \
    --contact-email sudershan@uchicago.edu \
    --project-id ff6bae42-f7a6-4833-ac92-792e5b9a69fa

sudo globus-connect-server node setup --ip-address 192.5.87.217

sudo systemctl reload apache2

sudo globus-connect-server login localhost

# Sanity
sudo globus-connect-server endpoint show

sudo globus-connect-server storage-gateway create posix "Posix /home/cc/globus_connect" \
    --domain uchicago.edu \
    --user-allow sudershan
    # --restrict-paths file:path-restriction.json \


sudo globus-connect-server collection create \
    0a2f6511-ac8a-4211-8130-53b0f8b3bdd6 \
    / "POSIX uchicago.org only directory" \
    --organization 'UChicago Org' \
    --contact-email sudershan@uchicago.edu \
    --keywords uchicago.org,home \
    --allow-guest-collections \
    --sharing-restrict-paths file:sharing_restrictions.json \
    --user-message "Tape storage: Do not upload small files" \
    --enable-https


# Personal endpoint
"e083a1b8-407a-11ee-b696-812118bf21b5"

# Server replacement
"6c0cf3be-4086-11ee-b696-812118bf21b5"