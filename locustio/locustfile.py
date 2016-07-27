from locust import HttpLocust, TaskSet, task
import json
import requests

class UserBehavior(TaskSet):
    
    #last_added 
    
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def login(self):
        """ Run on start for every Locust hatched """
        payload = {"username":"xxx", "password":"xxx"}
        headers = {'content-type': 'application/json'}
        self.client.post('/api/v1/user/login/', data=json.dumps(payload), headers=headers, catch_response=True)

    @task(1)
    def get_sed(self):
        self.client.get("/api/v1/sed/")
        
    @task(2)
    def post_sed(self):
        payload = {"brief_description": "locust_swarm_post", "draft": 1, "narrative": "", "public": 0, "related_brain_regions": [], "title": "locust_swarm_post", "type": "generic"}
        headers = {'content-type': 'application/json'}
        response = self.client.post("/api/v1/sed/", data=json.dumps(payload), headers=headers, catch_response=True)
        
    @task(3)
    def search_sed(self):
        self.client.get("/api/v1/sed/search/?format=json&q=mirror")
        

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait=5000
    max_wait=9000
