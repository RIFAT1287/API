from fastapi import FastAPI, HTTPException
from db import DB
from config import C
from bson.objectid import ObjectId

app = FastAPI()
token = C.TOKEN
bot_id = token.split(':')[0]
dbo = DB(collection_name=C.DB_NAME)

@app.get("/balance/{telegram_user_id}")
async def get_balance(telegram_user_id: str):
    try:
        # Ensure the user exists in the database
        user = telegram_user_id
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch user properties from the database or set defaults
        sol = dbo.get_property("sol", user) or 0
        solax = dbo.get_property("solax", user) or 0
        sol_mine = dbo.get_property("sol_mine", user) or 0
        ghs = dbo.get_property("ghs", user) or 1

        # Format the values to maintain precision
        fsol = f"{sol:.9f}"
        fsol_mine = f"{sol_mine:.9f}"

        # Log the data being returned for debugging purposes
        print(f"User: {user}, SOL: {fsol}, SOLAX: {solax}, Mining SOL: {fsol_mine}, GHS: {ghs}")

        # Return the user's balance information
        return {
            "sol_balance": fsol,
            "solax_balance": solax,
            "sol_mining_balance": fsol_mine,
            "ghs": ghs
        }

    except Exception as e:
        # Log the exception for debugging
        print(f"Error fetching balance for user {telegram_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
