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
    --owner vhayot@uchicago.edu \
    --contact-email vhayot@uchicago.edu \
    --project-id 3d66123c-327c-4c22-8c41-a1662b623b83

sudo globus-connect-server node setup # --ip-address 127.0.0.1

sudo systemctl reload apache2

sudo globus-connect-server login localhost

# Sanity
sudo globus-connect-server endpoint show

sudo globus-connect-server storage-gateway create posix "Posix /dsaas_storage" \
    --domain uchicago.edu \
    --user-allow vhayot
    # --restrict-paths file:path-restriction.json \


sudo globus-connect-server collection create \
    9476821a-2a10-47aa-be57-453a3617d69f \
    / "POSIX uchicago.org only directory" \
    --organization 'UChicago Org' \
    --contact-email vhayot@uchicago.edu \
    --keywords uchicago.org,home \
    --allow-guest-collections \
    --sharing-restrict-paths file:path_restrictions.json \
    --user-message "Tape storage: Do not upload small files" \
    --enable-https


# Personal endpoint
"e083a1b8-407a-11ee-b696-812118bf21b5"

# Server replacement
"6c0cf3be-4086-11ee-b696-812118bf21b5"
