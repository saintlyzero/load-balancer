import docker
import uvicorn
import requests

from typing import List
from docker.models.containers import Container
from docker.client import DockerClient
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

IMAGE_NAME = "flask_docker"
MEMORY_LIMIT = "140m" # memory ligit of each container
SERVER_PORT = 5000 # container exposed port
LB_PORT_START = 9000 # load-balancer port to bind with container
FAST_API_PORT = 8000 
INITIAL_NODE_COUNT = 3 # number of containers of load-balancers to start with
HEALTH_CHECK_TIME = 10  # seconds to wait before executing health-check


class Node:
    """Represent a server node in the load-balancer
    """
    def __init__(self, client: DockerClient, host_port: int) -> None:
        self.client = client
        self.host_port = host_port
        self.container: Container = None

    def power_on(self):
        """Start a docker container in detached mode
        """
        self.container = self.client.containers.run(
            IMAGE_NAME, "", detach=True, mem_limit=MEMORY_LIMIT, ports={f'{SERVER_PORT}/tcp': self.host_port})

    def power_off(self):
        """Stop and delete the docker container
        """
        self.container.stop()
        self.container.remove(force=True)

    def get_memory_usage(self) ->  float:
        """Calculate current memory utilization of the container 

        Returns:
            float: memory utilization percentage
        """
        stats = self.container.stats(stream=False)
        memory_used = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        return (memory_used / memory_limit) * 100


class LoadBalancer:
    def __init__(self, node_count: int) -> None:
        self.node_count = node_count
        self.nodes: List[Node] = []
        self.client = docker.from_env()

    def start_nodes(self):
        """Start all nodes on different ports
        """
        for i in range(self.node_count):
            node = Node(self.client, LB_PORT_START+i)
            node.power_on()
            self.nodes.append(node)

    def delete_nodes(self):
        """Delete all nodes from the load-balancer.
        """
        print("--Deleteing nodes--")
        for node in self.nodes:
            node.power_off()

    def health_check(self):
        """Run health-check for all the nodes
        """
        for itr, node in enumerate(self.nodes):
            print(f"Node {itr} : {node.get_memory_usage()}")


lb = LoadBalancer(INITIAL_NODE_COUNT)
app = FastAPI(title="Load Balancer")




@app.on_event("startup")
async def startup_event():
    print("Starting nodes")
    lb.start_nodes()


@app.on_event("startup")
@repeat_every(seconds=HEALTH_CHECK_TIME)
def health_check() -> None:
    print("starting health check")
    lb.health_check()


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down nodes")
    lb.delete_nodes()


@app.get("/api")
async def get_api():
    response = requests.get(f'http://localhost:{LB_PORT_START}/')
    return response.content.decode()



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=FAST_API_PORT, reload=True)
