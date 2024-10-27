from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import DB
from config import C
from bson.objectid import ObjectId

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
    

@app.get("/")
async def home():
    response_data = {
        "message": "Welcome to SolApi",
        "status": "success",
        "version": "1.0"
    }
    return response_data

@app.get("/balance", response_model=UserBalancesResponse)
async def get_balance(user: int):
    try:
        user = user
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        ton_balance = dbo.get_property(user, "ton") or 0
        tronix_balance = dbo.get_property(user, "tonx") or 0
        mined_ton = dbo.get_property(user, "mined_ton") or 0
        hash_power= dbo.get_property(user, "ghs") or 1
        status= dbo.get_property(user, "status") or "start"
        
        response_data = {
            "ton_balance": ton_balance,
            "tronix_balance": tronix_balance,
            "hase_power": hash_power,
            "mined_ton": mined_ton,
            "status": status,
            
        }
        return response_data

    except Exception as e:
        print(f"Error fetching balance for user {user}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/mining_balance/{telegram_user_id}")
async def get_mining_balance(telegram_user_id: str):
    try:
        user = telegram_user_id
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        sol_mine = dbo.get_property(user, "sol_mine") or 0
        fsol_mine = f"{sol_mine:.9f}"
        return {"mining_balance": fsol_mine}

    except Exception as e:
        print(f"Error fetching mining balance for user {telegram_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/update_balance/{telegram_user_id}")
async def update_mining_balance(telegram_user_id: str, balance_update: MiningBalanceUpdate):
    try:
        user = telegram_user_id
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the mining balance for the user
        mining_balance = balance_update.mining_balance
        dbo.set_property(user, "sol_mine", mining_balance)
        fsol_mine = f"{mining_balance:.9f}"

        return {"success": True, "mining_balance": fsol_mine}

    except Exception as e:
        print(f"Error updating mining balance for user {telegram_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/claim/{telegram_user_id}")
async def claim(telegram_user_id: str):
    try:
        user = telegram_user_id
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Fetch user's SOL and mining balance
        sol = dbo.get_property(user, "sol") or 0
        sol_mine = dbo.get_property(user, "sol_mine") or 0
        
        # Add the mining balance to SOL balance and reset mining balance to 0
        new_sol_balance = sol + sol_mine
        dbo.set_property(user, "sol", new_sol_balance)  # Update SOL balance
        dbo.set_property(user, "sol_mine", 0)  # Reset mining balance to 0

        return {"success": True, "sol_balance": new_sol_balance}

    except Exception as e:
        print(f"Error processing claim for user {telegram_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
