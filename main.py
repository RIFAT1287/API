from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import DB
from config import C
from bson.objectid import ObjectId
from datetime import datetime
import time

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
        dbo.set_property(user, "ghs", hash)
        status= dbo.get_property(user, "status") or "start"
        
        response_data = {
            "ton_balance": ton_balance,
            "tronix_balance": tronix_balance,
            "hase_power": hash,
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
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
    
