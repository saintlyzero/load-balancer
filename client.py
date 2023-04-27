import requests
import time 


INTERVAL = 0.5
ENDPOINT = "http://localhost:8000/api"

def send_req():
    cnt = 0
    while True:
        response = requests.get(ENDPOINT)
        print(f"Request {cnt} completed")
        cnt += 1
        time.sleep(INTERVAL)

if __name__ == "__main__":
    send_req()