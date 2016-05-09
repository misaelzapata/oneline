# -*- coding: utf-8 -*-

"""
Author: Matias Bastos <matias.bastos@gmail.com>
"""
import logging
from itsdangerous import TimestampSigner

from config import get_config

CONF = get_config()
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)

def get_operator_id(operator_cn):
    CONF = get_config()
    signer = TimestampSigner(CONF.SECRET)
    try:
        cookie = operator_cn.get_cookie(CONF.OPERATOR_ID_COOKIE)
        if cookie is None:
            raise Exception('Cookie not found')
        operator_id = signer.unsign(cookie, max_age=CONF.AUTH_EXPIRY)
        return operator_id
    except Exception as e:
        logging.error('Login error: %s.', e)
        return False
