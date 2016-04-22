# -*- coding: utf-8 -*-

import os
import json
from importlib import import_module

def get_config(config=None):
    if config is None:
        config = os.environ['ONELINE_CONFIG']
    Config = getattr(import_module('config'), config)
    configuration = Config()
    return configuration


class Config(object):
    DEBUG = True  #os.environ['DEBUG']
    MONGODB_DB = '' #os.environ['MONGODB_DB']
    MONGODB_USER = '' #os.environ['MONGODB_USER']
    MONGODB_PASS = '' #os.environ['MONGODB_PASS']
    MONGODB_HOST = '' #os.environ['MONGODB_HOST']
    MONGODB_PORT = '' #os.environ['MONGODB_PORT']
    RABBITMQ_HOST = '' #os.environ['REDIS_DATABASE']


class DevelopmentConfig(Config):
    DEBUG = True
    MONGODB_DB = 'oneline'
    MONGODB_HOST = 'mongo'
    MONGODB_PORT = 27017
    RABBITMQ_HOST = 'localhost'
    
