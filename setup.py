import os
import config
import sqlite3 as lite

#Creates the target folder for our data
#Initialise the main database if this isn't already done.
#Call all the classes we might use, and set those up, if necessary.

if not os.path.exists(config.pathToData):
    os.makedirs(config.pathToData)

print "Configuring psych database"
con = lite.connect(config.pathToData + 'psych.db')
cur = con.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS sessions (user integer primary key autoincrement, sessionid varchar(255));')
cur.execute('CREATE TABLE IF NOT EXISTS conversation_state (sessionid varchar(255) primary key, state integer);')
#cur.execute('CREATE TABLE IF NOT EXISTS qa (userid integer, dataset varchar(255), dataitem varchar(255), detail varchar(255), answered integer, asked_last integer, answer varchar(255), PRIMARY KEY (userid, dataset, dataitem, detail));')
cur.execute('CREATE TABLE IF NOT EXISTS qa (qid integer PRIMARY KEY AUTOINCREMENT, userid integer, dataset varchar(255), dataitem varchar(255), detail varchar(255), answered integer, asked_last integer, answer varchar(255));')
cur.execute('CREATE TABLE IF NOT EXISTS keystrokes (kid INTEGER PRIMARY KEY AUTOINCREMENT, qid INTEGER, keystrokes VARCHAR, date DATETIME);');
cur.close()
con.commit()

os.chmod(config.pathToData + 'psych.db', 0666) #0 makes it octal
