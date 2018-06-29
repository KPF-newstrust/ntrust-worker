import os
import logging
import pymongo

mgo_cli = None
mgo_db = None

def connect():
    global mgo_cli, mgo_db
    mgo_cli = pymongo.MongoClient(os.environ["MONGO_URL"])
    mgo_db = mgo_cli[os.environ["MONGO_DB"]]
    mgo_cli.server_info() # will raise exception if failed
    logging.info("Successfully connected to MongoDB %s", os.environ["MONGO_URL"])

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
