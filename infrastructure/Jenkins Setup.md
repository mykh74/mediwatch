# Jenkins Setup
This file describes how jenkins needs be setup in order to run this pipeline

### OS
This pipeline assumes jenkins runs on Linux and uses bash commands. Can be run on Windows by installing jenkins on the WSL
Hasn't been tested on mac.

### Jenkins Credentials
postgres-user-account - a username/password pair for postgress access. can be anything
postgres-admin-password - a secret text containing the password for the postgres admin account
local-kube-config - a secret file containing the .kube/config file, used to authenticate with kubernetes. Copy it from your local user account for local kubernetes use
    NOTE: YOUR config FILE WILL USE THE SERVER URL - server: https://127.0.0.1:{PORT}
    However Jenkins needs the internal address, which is - server: https://host.docker.internal:{PORT}
    make sure you make this change in the config before storing it as a secret in jenkins



### Jenkins plugins
Docker Pipeline - allows docker based agents

### Tool Requirements for Jenkins node
jq - `apt get jq` - json processing
docker - `apt get docker` - containerization
kubectl - `apt get kubectl` - cluster management