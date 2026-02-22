# Jenkins Setup
This file describes how jenkins needs be setup in order to run this pipeline

### OS
This pipeline assumes jenkins runs on Linux and uses bash commands. Can be run on Windows by installing jenkins on the WSL
Hasn't been tested on mac.

### Jenkins plugins
Docker Pipeline - allows docker based agents

### Tool Requirements for Jenkins node
jq - `apt get jq` - json processing
docker - `apt get docker` - containerization
kubectl - `apt get kubectl` - cluster management