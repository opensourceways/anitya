#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
An instance of the Flask application.

This is intended to be run with the Flask CLI for development purposes only::

    $ export ANITYA_WEB_CONFIG=<config_file>
    $ export FLASK_DEBUG=1
    $ export FLASK_APP=<this_file>
    $ flask run --host 0.0.0.0 --port 5000
"""

from anitya.app import create
from gevent import pywsgi

if __name__ == "__main__":
    app = create()
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app)
    server.serve_forever()
