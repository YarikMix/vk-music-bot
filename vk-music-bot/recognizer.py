import json
import io

import requests
from acrcloud.recognizer import ACRCloudRecognizer


class Recognizer:
    def auth(self, config):
        recognizer_config = {
            "host": config["ACRCloud"]["host"],
            "access_key": config["ACRCloud"]["access_key"], 
            "access_secret": config["ACRCloud"]["secret_key"],
            "timeout": 10
        }
        self.recognizer = ACRCloudRecognizer(recognizer_config)

    def recognize(self, url):
        response = requests.get(url, stream=True)
        buffer = io.BytesIO(response.content).read()

        response = self.recognizer.recognize_by_filebuffer(buffer, 0)
        data = json.loads(response)

        status = data["status"]["msg"]
        if status == "Success":
            title = data["metadata"]["music"][0]["title"]
            artist = data["metadata"]["music"][0]["artists"][0]["name"]
            song = "{} - {}".format(artist, title)
            return song
        else:
            return False