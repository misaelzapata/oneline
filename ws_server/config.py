# -*- coding: utf-8 -*-

"""
Author: Matias Bastos <matias.bastos@gmail.com>
"""

import os
import logging
from importlib import import_module

DEFAULT_CONFIG = 'DevelopmentConfig'


def get_config(config=None):
    if config is None:
        if 'ONELINE_CONFIG' in os.environ:
            config = os.environ['ONELINE_CONFIG']
        else:
            config = DEFAULT_CONFIG
    Configuration = getattr(import_module('config'), config)
    configuration = Configuration()
    return configuration


class Config(object):
    """
    Base Config
    """
    LOGGING_LEVEL = logging.WARNING
    LOGGING_FORMAT = '%(asctime)s - %(levelname)s: %(message)s'
    PORT = '8080'
    OPERATOR_ID_COOKIE = 'operator'
    SECRET = "__GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"
    AUTH_EXPIRY = 8*60*60  # 8 hours
    MONGODB_DB = '' #os.environ['MONGODB_DB']
    MONGODB_USER = '' #os.environ['MONGODB_USER']
    MONGODB_PASS = '' #os.environ['MONGODB_PASS']
    MONGODB_HOST = '' #os.environ['MONGODB_HOST']
    MONGODB_PORT = '' #os.environ['MONGODB_PORT']
    RABBITMQ_HOST = '' #os.environ['REDIS_DATABASE']


class DevelopmentConfig(Config):
    """
    Dev Config
    """
    LOGGING_LEVEL = logging.INFO
    MONGODB_DB = 'oneline'
    MONGODB_HOST = 'mongo'
    MONGODB_PORT = 27017
    RABBITMQ_HOST = 'localhost'
