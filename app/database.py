import os
import sqlite3

from flask import g


# absolute path to db (abs path to directory this file is in) + db filename
DATABASE = os.path.join( os.path.dirname( os.path.abspath(__file__)), 'monster.db' )

# establish db connection
def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect(DATABASE)
		db.row_factory = sqlite3.Row
	return db
