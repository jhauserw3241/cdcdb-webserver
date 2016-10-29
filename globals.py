from hashids import Hashids
from sqlalchemy import create_engine
from datetime import datetime
from datetime import timedelta
import requests
import configparser
import binascii
import hashlib

# Contains methods useful all over the app

# base58_hashids is used for obfuscating integer identifiers into
# short strings of characters to prevent enumeration

# password related functions keep the password generation/checking logic
# in one place

# sqltimestamp_to_relative converts a sql-formatted date-time string into
# a relative time ("4 hours ago") for nice human consumption

config = configparser.ConfigParser()
config.read("config.ini")

class globals:
    base58_hashids = Hashids(
        alphabet=config['b58']['alphabet'],
        salt=config['b58']['salt'],
        min_length=int(config['b58']['min_length']))
    config = config
    db_engine = create_engine('postgresql://webapp:imawebapp@localhost/ksucdc')

    def encode_id(thing, column=None):
        if column == None: column='id'
        thing[column] = globals.base58_hashids.encode(thing[column])
        return thing

    def decode_id(thing):
        thing['id'] = globals.base58_hashids.decode(thing['id'])
        return thing

    def hash_password(plain_text, salt):
        plain_text = bytes(plain_text, 'utf-8')
        salt = bytes(salt, 'utf-8')
        hash = hashlib.pbkdf2_hmac('sha256', plain_text, salt, int(config['common']['hash_rounds']))
        hash = binascii.hexlify(hash)
        return hash

    def check_password(plain_text, cipher_text, salt):
        plain_text = bytes(plain_text, 'utf-8')
        salt = bytes(salt, 'utf-8')
        hash = hashlib.pbkdf2_hmac('sha256', plain_text, salt, int(config['common']['hash_rounds']))
        hash = binascii.hexlify(hash)
        return hash == cipher_text

    def sqltimestamp_to_relative(timestamp):
        now = datetime.utcnow()
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        diff = now - timestamp
        sec_in_min = 60
        sec_in_hr = sec_in_min * 60
        sec_in_day = sec_in_hr * 24
        sec_in_wk = sec_in_day * 7
        sec_in_mon = sec_in_day * 30
        sec_in_yr = sec_in_day * 365
        diff = diff.seconds + diff.days * sec_in_day
        if diff < sec_in_min:
            return "just now"
        elif diff < sec_in_hr:
            value = diff//sec_in_min
            value = str(value) + " minute" + ("s" if value!=1 else "")
        elif diff < sec_in_day:
            value = diff//sec_in_hr
            value = str(value) + " hour" + ("s" if value!=1 else "")
        elif diff < sec_in_wk:
            value = diff//sec_in_day
            value = str(value) + " day" + ("s" if value!=1 else"")
        elif diff < sec_in_mon:
            value = diff//sec_in_wk
            value = str(value) + " week" + ("s" if value!=1 else"")
        elif diff < sec_in_yr:
            value = diff//sec_in_mon
            value = str(value) + " month" + ("s" if value!=1 else"")
        elif diff < sec_in_yr*6:
            value = diff//sec_in_yr
            value = str(value) + " year" + ("s" if value!=1 else"")
        else:
            value = "a long time"
        return value + " ago"

    def current_datetime(frmt="%x %X", utc=False):
        if utc:
            return datetime.utcnow().strftime(frmt)
        else:
            return datetime.now().strftime(frmt)
