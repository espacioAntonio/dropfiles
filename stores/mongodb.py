import json

from pymongo import MongoClient
from oauth2client.client import OAuth2Credentials


class CredentialsStore(object):
    """docstring for CredentialsStore"""

    def __init__(self):
        super(CredentialsStore, self).__init__()
        self.client = MongoClient(
            host='localhost', port=27017, username="admin", password="admin")
        self.dropfilesdb = self.client['dropfiles']
        self.credentials = self.dropfilesdb['credentials']

    def __getitem__(self, sub):
        data = self.credentials.find_one({"id_token.sub": sub}, {'_id': 0})
        return json.dumps(dict(data))

    def __setitem__(self, sub, data):
        data = json.loads(data)
        print("sub:current: {}".format(data['id_token']['sub']))
        self.credentials.replace_one({"id_token.sub": sub}, data, upsert=True)

    def __delitem__(self, sub):
        self.credentials.delete_one({"id_token.sub": sub})
