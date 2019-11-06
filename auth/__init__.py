import os

from urllib.parse import urlparse

from flask_oidc import OpenIDConnect
from keycloak import KeycloakOpenID
from ..stores.mongodb import CredentialsStore


mongo_credentials_store = CredentialsStore()


def initOIDC(app):
    app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
    app.config["OIDC_COOKIE_SECURE"] = False
    app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
    app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
    return OpenIDConnect(app, credentials_store=mongo_credentials_store)


def keycloakLogout(oidc):
    keycloak_netloc = urlparse(oidc.client_secrets["issuer"]).netloc
    keycloak_realm = oidc.client_secrets["issuer"].split("/")[-1]
    keycloak_openid = KeycloakOpenID(server_url="https://{}/auth/".format(keycloak_netloc),
                                     client_id=oidc.client_secrets["client_id"],
                                     realm_name=keycloak_realm,
                                     client_secret_key=oidc.client_secrets["client_secret"],
                                     verify=False)
    keycloak_openid.logout(oidc.get_refresh_token())


def get_oidc_dir(here, oidc):
    user_openid = oidc.user_getfield('sub')
    if not user_openid:
        return make_response(('sub of user is required', 400))
    save_dir = os.path.join(here, "tmp", user_openid)
    os.makedirs(save_dir, exist_ok=True)
    email_file = "{}/__info__{}__info__".format(
        save_dir, oidc.user_getfield('email'))
    open(email_file, 'a').close()
    return save_dir


def get_public_dir(here):
    return os.path.join(here, "tmp", "public")
