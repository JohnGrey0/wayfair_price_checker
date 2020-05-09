import pymongo


class mongo:
    def __init__(self, database: str, collection: str):
        self.client = pymongo.MongoClient()
        self.database = self.client[database]
        self.collection = self.database[collection]
    
    def insert_one(self, payload: dict):
        self.collection.insert_one(payload).inserted_id

    def query_match(self, column: str, value: str):
        query = { column: value}
        return self.collection.find(query)
    
    def update(self, query: str, new_values: dict):
        # Example: 
        # query = { "address": "Valley 345" }
        # new_values = { "$set": { "address": "Canyon 123" } }
        return self.collection.update_one(query, new_values)
    
if __name__ == '__main__':
    db = mongo(database='mydbs', collection='price_checker')
    print(db.query_match(column='target', value=175))
    