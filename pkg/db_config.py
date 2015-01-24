#!/usr/bin/env python

import MySQLdb

def db_connection():
    db = MySQLdb.connect(host="your.hostname.com",
                     user="myuser",
                     passwd="mypass",
                     db="BingRewards")
    db.autocommit(True)
    return db
