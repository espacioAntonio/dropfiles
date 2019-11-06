#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import logging
import logging.config
import yaml

here = os.path.abspath(os.path.dirname(__file__))
log = logging.getLogger('dropfiles')

try:
    with open(os.path.join(here, "conf/dropfiles.logging.yaml")) as f:
        logging.config.dictConfig(yaml.load(f, yaml.SafeLoader))
except Exception as err:
    print(f"Could not load logging config: {err}")
else:
    log.info("Log configuration applied")

os.makedirs(os.path.join(here, "tmp"), exist_ok=True)
os.makedirs(os.path.join(here, "logs"), exist_ok=True)

security = "OIDC"
keycloak = True
