from pymongo import MongoClient
from config import C
class DB:
    def __init__(self, collection_name, database_name=C.DB_NAME):
        uri = C.DB_URL
        self.client = MongoClient(uri)
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]

    def _load_data(self, user_id):
        user_data = self.collection.find_one({"user_id": user_id})
        return user_data if user_data else {}

    def _save_data(self, user_id, user_data):
        self.collection.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )
        
        
    def add_transaction(self, user_id, transaction):
        user_data = self._load_data(user_id)
        transactions = user_data.get("transactions", [])
        
        transactions.append(transaction)
        user_data["transactions"] = transactions

        self._save_data(user_id, user_data)    
        
    def update_boost_data(self, user_id, user_data):
        
        data = self._load_data(user_id)
        bs_data = data.get("boost_data", [])

        
        bs_data.append(user_data)
        data["boost_data"] = bs_data

        self._save_data(user_id, data)    

    def get_property(self, user_id, property_name, default=None):
        user_data = self._load_data(user_id)
        return user_data.get(property_name, default)

    def set_property(self, user_id, property_name, value):
        user_data = self._load_data(user_id)
        user_data[property_name] = value
        self._save_data(user_id, user_data)

    def add_value(self, user_id, property_name, amount):
        user_data = self._load_data(user_id)
        current_value = user_data.get(property_name, 0)
        user_data[property_name] = current_value + amount
        self._save_data(user_id, user_data)

    def cut_value(self, user_id, property_name, amount):
        user_data = self._load_data(user_id)
        current_value = user_data.get(property_name, 0)
        user_data[property_name] = max(0, current_value - amount)
        self._save_data(user_id, user_data)

    def get_data(self, user_id):
        return self._load_data(user_id)
    
    def is_exists(self, user_id):
        return self.collection.find_one({"user_id": int(user_id)}) is not None
    
    def is_email_exists(self, email):
        return self.collection.find_one({"email": email}) is not None
    
    def get_all_user_ids(self):
        user_ids = [user["user_id"] for user in self.collection.find({}, {"user_id": 1})]
        return user_ids
    
    def get_user_count(self):
        count = self.collection.count_documents({})
        return count


    def add_list(self, user_id, property_name, item):
        user_data = self._load_data(user_id)
        current_list = user_data.get(property_name, [])
        current_list.append(item)
        user_data[property_name] = current_list
        self._save_data(user_id, user_data)

    def remove_list(self, user_id, property_name, item):
        user_data = self._load_data(user_id)
        current_list = user_data.get(property_name, [])
        if item in current_list:
            current_list.remove(item)
        user_data[property_name] = current_list
        self._save_data(user_id, user_data)



    def get_list(self, user_id, property_name):
        user_data = self._load_data(user_id)
        return user_data.get(property_name, [])
