#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import logging
import yaml

import dropfiles.config

from urllib.parse import urlparse

from flask import render_template, Blueprint, request, make_response, Flask, redirect, url_for
from werkzeug.utils import secure_filename
from flask_oidc import OpenIDConnect
from keycloak import KeycloakOpenID

here = os.path.abspath(os.path.dirname(__file__))
blueprint = Blueprint('templated', __name__, template_folder='templates')
log = logging.getLogger('dropfiles')

app = Flask('dropfiles',
                  template_folder=os.path.join(here, 'templates'))
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["SECRET_KEY"] = "{{ LONG_RANDOM_STRING }}"
oidc = OpenIDConnect(app)

keycloak_netloc = urlparse(oidc.client_secrets["issuer"]).netloc
keycloak_realm = oidc.client_secrets["issuer"].split("/")[-1]
keycloak_openid = KeycloakOpenID(server_url="https://{}/auth/".format(keycloak_netloc),
                    client_id=oidc.client_secrets["client_id"],
                    realm_name=keycloak_realm,
                    client_secret_key=oidc.client_secrets["client_secret"],
                    verify=False)


@blueprint.route('/')
@blueprint.route('/index')
@oidc.require_login
def index():
    # Route to serve the upload form
    return render_template('index.html',
                           page_name='Main',
                           project_name="dropfiles")


@blueprint.route('/upload', methods=['POST'])
@oidc.require_login
def upload():
    file = request.files['file']

    # save_path = os.path.join(config.data_dir, secure_filename(file.filename))
    user_openid = oidc.user_getfield('sub')
    if not user_openid:
        return make_response(('sub of user is required', 400))
    save_dir = os.path.join(here, "tmp", user_openid)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, secure_filename(file.filename))
    current_chunk = int(request.form['dzchunkindex'])

    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(('File already exists', 400))

    try:
        with open(save_path, 'ab') as f:
            f.seek(int(request.form['dzchunkbyteoffset']))
            f.write(file.stream.read())
    except OSError:
        # log.exception will include the traceback so we can see what's wrong
        log.exception('Could not write to file')
        return make_response(("Not sure why,"
                              " but we couldn't write the file to disk", 500))

    total_chunks = int(request.form['dztotalchunkcount'])

    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        if os.path.getsize(save_path) != int(request.form['dztotalfilesize']):
            log.error(f"File {file.filename} was completed, "
                      f"but has a size mismatch."
                      f"Was {os.path.getsize(save_path)} but we"
                      f" expected {request.form['dztotalfilesize']} ")
            return make_response(('Size mismatch', 500))
        else:
            log.info(f'File {file.filename} has been uploaded successfully')
    else:
        log.debug(f'Chunk {current_chunk + 1} of {total_chunks} '
                  f'for file {file.filename} complete')

    return make_response(("Chunk upload successful", 200))

@app.route("/login")
@oidc.require_login
def login():
    return redirect("/")

@app.route("/logout")
def logout():
    keycloak_openid.logout(oidc.get_refresh_token())
    oidc.logout()
    return redirect("/")

app.register_blueprint(blueprint)
