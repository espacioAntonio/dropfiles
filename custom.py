#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import os

from flask import render_template, Blueprint, request, make_response, Flask, redirect, url_for
from werkzeug.utils import secure_filename

import logging.config
import yaml
# from dropfiles.config import config

from flask_oidc import OpenIDConnect

here = os.path.abspath(os.path.dirname(__file__))
blueprint = Blueprint('templated', __name__, template_folder='templates')
log = logging.getLogger('dropfiles')

try:
    with open(os.path.join(here, "conf/dropfiles.logging.yaml")) as f:
        logging.config.dictConfig(yaml.load(f, yaml.SafeLoader))
except Exception as err:
    print(f"Could not load logging config: {err}")
else:
    log.info("Log configuration applied")

app = Flask('dropfiles',
                  template_folder=os.path.join(here, 'templates'))
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["SECRET_KEY"] = "{{ LONG_RANDOM_STRING }}"
oidc = OpenIDConnect(app)

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
    save_path = "{}/tmp/{}".format(here, secure_filename(file.filename))
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

app.register_blueprint(blueprint)

@app.route("/login")
@oidc.require_login
def login():
    return redirect("/")

@app.route("/logout")
def logout():
    oidc.logout()
    return redirect("/")

