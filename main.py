from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import DB
from config import C
from bson.objectid import ObjectId
from datetime import datetime
import time
from typing import List
import json

app = FastAPI()
token = C.TOKEN
bot_id = token.split(':')[0]
dbo = DB(collection_name=C.DB_NAME)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MiningBalanceUpdate(BaseModel):
    mining_balance: float

class UserBalancesResponse(BaseModel):
    ton_balance: float
    tronix_balance: float
    hase_power: float
    mined_ton: float
    status: str
    
class UpdateMiningStatus(BaseModel):
    status: str    

class MinedTonResponse(BaseModel):
    status: str
    mined_ton: float

class ClaimTonResponse(BaseModel):
    status: str
    message: str
    
class HasePowerUpdateRequest(BaseModel):
    user: int
    hase_power: float

class HasePowerUpdateResponse(BaseModel):
    success: bool
    error: str = None
 
class Transaction(BaseModel):
    user_id: int
    transaction: dict  

class TranDataResponse(BaseModel):
    tran_data: List[dict] = []
 
class BoostData(BaseModel):
    user_data: dict    


class BoostDataResponse(BaseModel):
    boost_data: List[dict] = []
    

class UpdateBalanceRequest(BaseModel):
    user_id: int
    coin: str
    amount: float
    set_coin: str


    

@app.get("/")
async def home():
    response_data = {
        "message": "Welcome to SolApi",
        "status": "success",
        "version": "1.0"
    }
    return response_data


@app.get("/balance", response_model=UserBalancesResponse)
async def get_balance(user: int, hash:int):
    try:
        user = user
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        ton_balance = dbo.get_property(user, "ton") or 0
        tronix_balance = dbo.get_property(user, "tonx") or 0
        mined_ton = dbo.get_property(user, "mined_ton") or 0
        ghs = dbo.get_property(user, "ghs")
        if ghs==None:
            ghs=hash
        status= dbo.get_property(user, "status") or "start"
        
        response_data = {
            "ton_balance": ton_balance,
            "tronix_balance": tronix_balance,
            "hase_power": ghs,
            "mined_ton": mined_ton,
            "status": status,
            
        }
        return response_data

    except Exception as e:
        print(f"Error fetching balance for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/update_mining_status", response_model=UpdateMiningStatus)
async def update_mining_status(user: int):
    try:
        dbo.set_property(user, "status", "active")
        dbo.set_property(user, "last_mined", datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
        return {"status": "success", "message": "Mining status updated successfully"}
        
    except Exception as e:
        print(f"Error changing status for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")    
    
@app.get("/update_mining", response_model=MinedTonResponse)
async def calculate_mined_ton(user: int, cps:float):
    try:
        status= dbo.get_property(user, "status") or "start"
        if not status == "active":
            raise HTTPException(status_code=404, detail="User not found or mining not active")
        current_time = time.time()
        last_mined_time = dbo.get_property(user, "last_mined")
        if last_mined_time is None:
            last_mined_time = current_time
        last_mined_timestamp = datetime.strptime(last_mined_time, '%Y/%m/%d %H:%M:%S').timestamp() 
    
        hase_power = dbo.get_property(user, "ghs") or 9
        coin_per_second = cps
    
        mining_duration = current_time - last_mined_timestamp
        mining_value_per_sec = hase_power * coin_per_second
        new_mined_ton = mining_value_per_sec * mining_duration
    
        mined_ton = dbo.get_property(user, "mined_ton") or 0    
        dbo.add_value(user, "mined_ton", new_mined_ton)
        dbo.set_property(user, "last_mined", datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
        updated_mined_ton=new_mined_ton + mined_ton
    
    
        return {"status": "success", "mined_ton": updated_mined_ton}

    except Exception as e:
        print(f"Error calculating mined TON for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
  
  
  
@app.get("/claim_ton", response_model=ClaimTonResponse)
async def claim_ton(user: int, mined_ton: float):
    try:
        user_balance = dbo.get_property(user, "ton") or 0
        updated_balance = user_balance + mined_ton
        dbo.set_property(user, "ton", updated_balance)
        dbo.set_property(user, "mined_ton", 0)
        return {"status": "success", "message": "TON claimed successfully."}
    except Exception as e:
        print(f"Error claiming TON for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update balance in database")   

    
  
@app.post("/update_hase_power", response_model=HasePowerUpdateResponse)
async def update_hase_power(data: HasePowerUpdateRequest):
    try:
        dbo.add_value(data.user, "ghs", data.hase_power)
        
        return {"success": True}
        
    except Exception as e:
        print(f"Error updating hase_power for user {data.user}: {e}")
        return {"success": False, "error": str(e)}
  
  
  
@app.post("/add_transection")
async def add_transaction_endpoint(transaction_data: Transaction):
    user_id = transaction_data.user_id
    transaction = transaction_data.transaction
    
    if not dbo.is_exists(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        dbo.add_transaction(user_id, transaction)
        return {"success": True, "message": "Transaction added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add transaction: {e}")
        
@app.get("/get_transaction")
async def get_boost_data(user: int):
    try:
        user_data = dbo.get_property(user, "transactions", default=[])
        return user_data
    except Exception as e:
        print(f"Error retrieving boost data for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve boost data")        

  
@app.post("/update_boost_data")
async def update_boost_data(data: BoostData):
    try:
        dbo.update_boost_data(bot_id, data.user_data)
        return {"status": "success", "message": "User data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user data:{e}") 
  
  
@app.get("/get_boost_data")
async def get_boost_data():
    try:
        user_data = dbo.get_property(bot_id, "boost_data", default=[])
        return user_data
    except Exception as e:
        print(f"Error retrieving boost data for user : {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve boost data")
        
@app.post("/update_balance")
async def update_balance(request: UpdateBalanceRequest):
    user_id = request.user_id
    coin = request.coin
    amount = float(request.amount)
    con = request.set_coin
    
    if coin == 'TON':
        prev = float(dbo.get_property(user_id, "ton") or 0)
        new_balance =prev - amount
        if new_balance < 0:
            raise HTTPException(status_code=400, detail="Insufficient TON balance")
        dbo.set_property(user_id, "ton", new_balance)
    elif coin == con:
        prev = float(dbo.get_property(user_id, "tonx") or 0)
        new_balance =prev - amount
        if new_balance < 0:
            raise HTTPException(status_code=400, detail="Insufficient TRON balance")
        dbo.set_property(user_id, "tonx", new_balance)
    else:
        raise HTTPException(status_code=400, detail="Invalid coin type")

    return {"success": True}    


@app.post("/save_withdraw")
async def save_withdraw(data: dict):
    try:
        current_withdrawals = dbo.get_property(bot_id, "withdrawals", default=[])

        updated_withdrawals = current_withdrawals + [data]
        dbo.set_property(bot_id, "withdrawals", updated_withdrawals)
        

        return {"success": True}
    except Exception as e:
        print(f"Error saving withdraw data for user: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve boost data")
        
@app.get("/get_withdraw")
async def get_with():
    try:
        user_data = dbo.get_property(bot_id, "withdrawals", default=[])
        return user_data
    except Exception as e:
        print(f"Error retrieving boost data for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve boost data")            
@app.get("/update_friend_data")
async def update_friend_data(user_id: int, level: int, first_name: str, last_name: str, tronix: float, ghs: int):
    try:
        # Fetch existing friend data for the user
        friend_data = dbo.get_property(user_id, "friends_data", default={
            "friends_count": {
                "total_friends": 0,
                "level1": 0,
                "level2": 0,
                "level3": 0
            },
            "friends": []
        })

        # Update friends count based on the level
        friend_data["friends_count"]["total_friends"] += 1
        friend_data["friends_count"]["level" + str(level)] += 1


        # Add the new friend to the list with their details
        friend_data["friends"].append({
            "level": level,
            "name": f"{first_name} {last_name}",
            "tronix": tronix,
            "hase_power": ghs
        })

        # Save the updated friend data back to the database
        dbo.set_property(user_id, "friends_data", friend_data)

        return {"success": True}
    except Exception as e:
        print(f"Error updating friend data: {e}")
        raise HTTPException(status_code=500, detail="Failed to update friend data")


@app.get("/get_friend_data")
async def get_friend_data(user_id: int):
    try:
        friend_data = dbo.get_property(user_id, "friends_data", default={
            "friends_count": {
                "total_friends": 0,
                "level1": 0,
                "level2": 0,
                "level3": 0
            },
            "friends": []
        })

        return friend_data
    except Exception as e:
        print(f"Error retrieving friend data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve friend data")

@app.get("/ref_bonus")
async def ref_bonus(user_id: int, tronix: float, ghs: float):
    try:
        dbo.add_value(user_id, "ton", tronix)
        dbo.add_value(user_id, "ghs", ghs)
        return {"success": True}
    except Exception as e:
        print(f"Error retrieving friend data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve friend data")
        
@app.get("/setrefer")
async def ref_set(user_id: int, ref: int):
    try:
        dbo.set_property(user_id, "referby", ref)
       
        return {"success": True}
    except Exception as e:
        print(f"Error adding ref for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to set ref")
        
@app.get("/getrefer")
async def ref_get(user_id: int):
    try:
        ido = dbo.get_property(user_id, "referby") or None
       
        return ido
    except Exception as e:
        print(f"Error get ref for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to set ref")
        
@app.get("/save_transaction")
async def save_tran(user_id: int, tronix_reward: float):
    
    time = datetime.now().strftime('%H:%M:%S')
    date = datetime.now().strftime('%d/%m/%Y')

    tronix_data = {
        "date_time": {
            "time": time,
            "date": date
        },
        "sum": {
            "tronix": tronix_reward
        },
        "type": "Bonus",
        "status": "completed"
    }
    print(tronix_data)
    try:
        dbo.add_transaction(user_id, tronix_data)

        return {"success": True, "message": "Transaction added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add transaction: {e}")
