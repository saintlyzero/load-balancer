import docker
import uvicorn
import requests

from typing import List
from docker.models.containers import Container
from docker.client import DockerClient
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

# load balancer
IMAGE_NAME = "flask_docker"
MEMORY_LIMIT = "140m" # memory ligit of each container
SERVER_PORT = 5000 # container exposed port
LB_PORT_START = 9000 # load-balancer port to bind with container
FAST_API_PORT = 8000 
INITIAL_NODE_COUNT = 3 # number of containers of load-balancers to start with
HEALTH_CHECK_TIME = 10  # seconds to wait before executing health-check

# auto-scaling
MAX_NODES = 10
MIN_NODES = 2
MAX_MEMORY_USAGE_THRESHOLD = 70 # memory usage threshold in percentage to scale up
MIN_MEMORY_USAGE_THRESHOLD = 30 # memory usage threshold in percentage to scale down   
SCALE_UP_NODE_COUNT = 2
SCALE_DOWN_NODE_COUNT = 2

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
    def __init__(self) -> None:
        self.nodes: List[Node] = []
        self.client = docker.from_env()
        self.last_used_port = LB_PORT_START

    def add_nodes(self, node_count:int):
        """Start all nodes on different ports
        """
        for _ in range(node_count):
            node = Node(self.client, self.last_used_port)
            self.last_used_port += 1
            node.power_on()
            self.nodes.append(node)

    def delete_nodes(self, node_count:int):
        while node_count and self.nodes:
            node = self.nodes.pop()
            self.last_used_port -= 1
            node.power_off()
            node_count -= 1

    def get_node_count(self) -> int:
        return len(self.nodes)

    def health_check(self):
        """Run health-check for all the nodes
        """

        memory_utilization = []
        for itr, node in enumerate(self.nodes):
            memory_utilized = node.get_memory_usage()
            memory_utilization.append(memory_utilized)
            print(f"Node {itr} : {memory_utilized}")

        # scale up
        if all(_memory > MAX_MEMORY_USAGE_THRESHOLD for _memory in memory_utilization):
            self.scale_up()

        # scale down
        elif all(_memory < MIN_MEMORY_USAGE_THRESHOLD for _memory in memory_utilization):
            self.scale_down()


    def scale_up(self):
        if self.get_node_count() + SCALE_UP_NODE_COUNT >= MAX_NODES:
            print(f"Maximum node count of {MAX_NODES} reached. Cannot add more nodes")
        else:
            print(f"Memory utilization of all nodes is over {MAX_MEMORY_USAGE_THRESHOLD}%")
            print(f"Auto Scaler: Adding {SCALE_UP_NODE_COUNT} nodes")
            self.add_nodes(SCALE_UP_NODE_COUNT)
            
    def scale_down(self):
        if self.get_node_count() - SCALE_DOWN_NODE_COUNT < MIN_NODES:
            print(f"Minimum node count of {MIN_NODES} reached. Cannot delete nodes")
        else:
            print(f"Memory utilization of all nodes is below {MIN_MEMORY_USAGE_THRESHOLD}%")
            print(f"Auto Scaler: Deleting {SCALE_DOWN_NODE_COUNT} nodes")
            self.delete_nodes(SCALE_DOWN_NODE_COUNT)

lb = LoadBalancer()
app = FastAPI(title="Load Balancer")


@app.on_event("startup")
async def startup_event():
    print("Starting nodes")
    lb.add_nodes(INITIAL_NODE_COUNT)


@app.on_event("startup")
@repeat_every(seconds=HEALTH_CHECK_TIME)
def health_check() -> None:
    print("starting health check")
    lb.health_check()


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down nodes")
    node_count = lb.get_node_count()
    lb.delete_nodes(node_count)


@app.get("/api")
async def get_api(num: int = 2):
    # response = requests.get(f'http://localhost:{LB_PORT_START}/')
    # return response.content.decode()
    return f"Square of {num} = {num**2}"



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=FAST_API_PORT, reload=True)
