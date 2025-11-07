import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

class Config:
  MONGO_USER = os.getenv("MONGO_USER")
  MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
  MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
  MONGO_DB = os.getenv("MONGO_DB")
  
  @staticmethod
  def get_db():
    uri = f"mongodb+srv://{Config.MONGO_USER}:{Config.MONGO_PASSWORD}@{Config.MONGO_CLUSTER}/?appName={Config.MONGO_DB}"
    
    client = MongoClient(uri, server_api=ServerApi('1'))
    
    db = client[Config.MONGO_DB]

    return db