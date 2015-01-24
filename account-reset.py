#!/usr/bin/env python

import MySQLdb

sys.path.append(os.path.join(os.path.dirname(__file__), "pkg"))
import db_config as DBConfig

db = DBConfig.db_connection()
cur = db.cursor()

cur.execute("UPDATE Accounts SET RanToday='NO', PointsEarned=0")
cur.execute("UPDATE Settings SET SentEmail='NO'")