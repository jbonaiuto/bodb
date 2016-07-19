from locust import HttpLocust, TaskSet, task
import json

class UserBehavior(TaskSet):
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def login(self):
        """ Run on start for every Locust hatched """
        payload = {"username":"xxx", "password":"xxx"}
        headers = {'content-type': 'application/json'}
        self.client.post('/api/v1/user/login/', data=json.dumps(payload), headers=headers, catch_response=True)

    @task(1)
    def profile(self):
        self.client.get("/api/v1/sed/")
        
    #@task(2)
    #def profile(self):
    #    self.client.get("/api/v1/user/logout/")

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait=5000
    max_wait=9000
