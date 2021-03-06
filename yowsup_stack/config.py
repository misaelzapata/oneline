# -*- coding: utf-8 -*-

import os
import json
from importlib import import_module

def get_config(config=None,
               credentials_json='credentials.json',
               credentials_index=0):
    if config is None:
        config = os.environ['ONELINE_CONFIG']
    Config = getattr(import_module('config'), config)
    configuration = Config()
    credentials = open(credentials_json).read()
    credentials = json.loads(credentials)
    configuration.CREDENTIALS = credentials[credentials_index]
    return configuration


class Config(object):
    SECRET_KEY = '' #os.environ['SECRET_KEY']
    DEBUG = True  #os.environ['DEBUG']
    MONGODB_DB = '' #os.environ['MONGODB_DB']
    MONGODB_USER = '' #os.environ['MONGODB_USER']
    MONGODB_PASS = '' #os.environ['MONGODB_PASS']
    MONGODB_HOST = '' #os.environ['MONGODB_HOST']
    MONGODB_PORT = '' #os.environ['MONGODB_PORT']
    REDIS_HOST = '' #os.environ['REDIS_HOST']
    REDIS_PORT = '' #os.environ['REDIS_PORT']
    REDIS_DATABASE = '' #os.environ['REDIS_DATABASE']
    RABBITMQ_HOST = '' #os.environ['REDIS_DATABASE']
    PHONE = '' #os.environ['PHONE']
    PASSWORD = '' #os.environ['PASSWORD']


class DevelopmentConfig(Config):
    SECRET_KEY = 'hi'
    DEBUG = True
    MONGODB_DB = 'oneline'
    MONGODB_HOST = 'mongo'
    MONGODB_PORT = 27017
    REDIS_HOST = 'redis' 
    REDIS_PORT = 6379
    REDIS_DATABASE = '0'
    RABBITMQ_HOST = 'localhost'
    
