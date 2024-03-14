#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""updatedb"""

import os

from alembic import command
from alembic.config import Config

alembic_config = os.path.join("/etc/alembic", "alembic.ini")

if alembic_config and os.path.isfile(alembic_config):
    alembic_cfg = Config(alembic_config)
    command.upgrade(alembic_cfg, "head")
