#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import logging
import yaml

import dropfiles.config

from flask import render_template, Blueprint, request, make_response, Flask, redirect, url_for
from werkzeug.utils import secure_filename

from .stores.mongodb import CredentialsStore
from .auth import initOIDC, keycloakLogout, get_oidc_dir, get_public_dir

here = os.path.abspath(os.path.dirname(__file__))
blueprint = Blueprint('templated', __name__, template_folder='templates')
log = logging.getLogger('dropfiles')

app = Flask('dropfiles',
            template_folder=os.path.join(here, 'templates'))
app.config["SECRET_KEY"] = "{{ LONG_RANDOM_STRING }}"

if dropfiles.config.security == "OIDC":
    oidc = initOIDC(app)


def authenticated(function):
    if dropfiles.config.security == "OIDC":
        return oidc.require_login(function)
    else:
        return function


@blueprint.route('/')
@blueprint.route('/index')
@authenticated
def index():
    # Route to serve the upload form
    if dropfiles.config.security == "OIDC":
        print(oidc._retrieve_userinfo())
    return render_template('index.html',
                           page_name='Main',
                           project_name="dropfiles")


@blueprint.route('/upload', methods=['POST'])
@authenticated
def upload():
    file = request.files['file']
    if dropfiles.config.security == "OIDC":
        save_dir = get_oidc_dir(here, oidc)
    elif dropfiles.config.security == "None":
        save_dir = get_public_dir(here)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, secure_filename(file.filename))

    if request.form:
        current_chunk = int(request.form['dzchunkindex'])
    else:
        current_chunk = 0
    log.debug(f"current_chunk: {current_chunk}")

    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(('File already exists', 400))

    try:
        with open(save_path, 'ab') as f:
            if request.form:
                f.seek(int(request.form['dzchunkbyteoffset']))
            else:
                f.seek(0)
            f.write(file.stream.read())
    except OSError:
        # log.exception will include the traceback so we can see what's wrong
        log.exception('Could not write to file')
        return make_response(("Not sure why,"
                              " but we couldn't write the file to disk", 500))

    if request.form:
        total_chunks = int(request.form['dztotalchunkcount'])
    else:
        total_chunks = 1

    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        if request.form:
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
@authenticated
def login():
    return redirect("/")


@app.route("/logout")
def logout():
    if dropfiles.config.security == "OIDC":
        if dropfiles.config.keycloak:
            keycloakLogout(oidc)
        oidc.logout()
    return redirect("/")


app.register_blueprint(blueprint)
