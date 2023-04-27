# Prerequisites
- Python3
- Docker

# Installation
- Install dependencies 
    - `pip install -r requirements.txt`
- Create Docker image
    - Go to `app` folder where the `Dockerfile` is located
    - Build image: `docker image build -t heavy_task .`

# Execute
- Run FastAPI server `python main.py`


# Handy Docker Commands
- List active docker containers
    - `docker ps`
- List docker images
    - `docker images`
- Stop docker container
    -  `docker stop <container-id>`
- Delete docker container
    -  `docker rm <container-id>`
- SSH into running docker container
    - `docker exec -it <container id/name> sh`