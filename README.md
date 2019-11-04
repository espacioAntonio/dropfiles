# Dropfiles

Upload files by chunks

## Requirements

```bash
# Mongo instance
docker run --name some-mongo -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=admin -d mongo
```

```json
// openidconnect config file
// ./client_secrets.json
{
    "web": {
	"issuer": "https://oidc.server.com/auth/realms/DropFiles",
        "auth_uri": "https://oidc.server.com/auth/realms/DropFiles/protocol/openid-connect/auth",
        "client_id": "dropfiles",
        "client_secret": "0fa02946-e839-1947-4c87-ba6b93b63a9e",
        "redirect_uris": [
            "http://YOUR_IP:5000/oidc_callback"
        ],
        "userinfo_uri": "https://oidc.server.com/auth/realms/DropFiles/protocol/openid-connect/userinfo",
        "token_uri": "https://oidc.server.com/auth/realms/DropFiles/protocol/openid-connect/token",
        "token_introspection_uri": "https://oidc.server.com/auth/realms/DropFiles/protocol/openid-connect/token/introspect"
    }
}

```

## Test
```bash
pip install -r requirements.txt

env FLASK_APP=custom.py flask run
```

## Original post

[Code calamity - Chris Griffith](https://codecalamity.com/uploading-large-files-by-chunking-featuring-python-flask-and-dropzone-js/)

