import logging
import pymongo

mgo_cli = None
mgo_db = None

def connect(config):
    global mgo_cli, mgo_db
    if "uri" not in config:
        raise SystemExit("Invalid mongo config section")
    mgo_cli = pymongo.MongoClient(config['uri'])
    mgo_db = mgo_cli[config['db']]
    mgo_cli.server_info() # will raise exception if failed
    logging.info("Successfully connected to MongoDB %s", config['uri'])

def close():
    global mgo_cli, mgo_db
    if mgo_cli is not None:
       mgo_cli.close()
       mgo_cli = None
       mgo_db = None

def get_db():
    if mgo_db is None:
        raise RuntimeError("MongoDB not connected")
    return mgo_db

def get_collection(collname):
    if mgo_db is None:
        raise RuntimeError("MongoDB not connected")
    return mgo_db[collname]
