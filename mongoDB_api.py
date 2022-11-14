""" Copyright (c) 2022 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_BASE_URL = os.environ['MONGODB_BASE_URL']
MONGO_DB_API_KEY = os.environ['MONGO_DB_API_KEY']
MONGO_DB_NAME= os.environ['MONGO_DB_NAME']
MONGO_DB_CLUSTER= os.environ['MONGO_DB_CLUSTER']

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Request-Headers': '*',
    'api-key': MONGO_DB_API_KEY, 
    }


def find_one(filter, collection):

    url = MONGODB_BASE_URL + "/action/findOne"
    
    payload = {
        "collection": collection,
        "database": MONGO_DB_NAME,
        "dataSource": MONGO_DB_CLUSTER,
        "filter": filter
    }
    
    response = requests.request("POST", url, headers=HEADERS, data=json.dumps(payload))
    return response.json()


def find_many(filter_rule, sort_rule, collection):
    
    url = MONGODB_BASE_URL + "/action/find"
    
    payload = {
        "collection": collection,
        "database": MONGO_DB_NAME,
        "dataSource": MONGO_DB_CLUSTER,
        "filter": filter_rule,
        "sort": sort_rule
    }
    
    response = requests.request("POST", url, headers=HEADERS, data=json.dumps(payload))
    return response.json()


def insert_one(dict_document, collection):

    url = MONGODB_BASE_URL + "/action/insertOne"
    
    payload = {
        "collection": collection,
        "database": MONGO_DB_NAME,
        "dataSource": MONGO_DB_CLUSTER,
        "document": dict_document
    }
    
    response = requests.request("POST", url, headers=HEADERS, data=json.dumps(payload))
    return response.json()


def insert_many(documents_list, collection):

    url = MONGODB_BASE_URL + "/action/insertMany"
    
    payload = {
        "collection": collection,
        "database": MONGO_DB_NAME,
        "dataSource": MONGO_DB_CLUSTER,
        "documents": documents_list
    }
    
    response = requests.request("POST", url, headers=HEADERS, data=json.dumps(payload))
    return response.json()


def update_one(documents_list, collection, filter):

    url = MONGODB_BASE_URL + "/action/updateOne"
    
    payload = {
        "dataSource": MONGO_DB_CLUSTER,
        "database": MONGO_DB_NAME,
        "collection": collection,
        "filter": filter,
        "update": documents_list,
        "upsert": True #Inserts new element if not available in the DB yet
        }
    
    response = requests.request("POST", url, headers=HEADERS, data=json.dumps(payload))
    return response.json()


def update_many(documents_list, collection, filter):

    url = MONGODB_BASE_URL + "/action/updateMany"
    
    payload = {
        "dataSource": MONGO_DB_CLUSTER,
        "database": MONGO_DB_NAME,
        "collection": collection,
        "filter": filter,
        "update": documents_list,
        "upsert": True #Inserts new element if not available in the DB yet
        }
    
    response = requests.request("POST", url, headers=HEADERS, data=json.dumps(payload))
    return response.json()


def deleteMany(collection, filter):

    url = MONGODB_BASE_URL + "/action/deleteMany"
    
    payload = {
        "dataSource": MONGO_DB_CLUSTER,
        "database": MONGO_DB_NAME,
        "collection": collection,
        "filter": filter
    }
    
    response = requests.request("POST", url, headers=HEADERS, data=json.dumps(payload))
    return response.json()

