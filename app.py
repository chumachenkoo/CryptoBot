import fastapi
import pydantic_models
import database.crud as crud
from fastapi.security import OAuth2PasswordRequestForm
from pydantic_models import Token, Admin
from security import *

api = fastapi.FastAPI()

@api.get("/items/")
async def read_items(token: str = fastapi.Depends(oauth2_scheme)):
    return {"token": token}


@api.get("/user/{user_id}")
def read_user(user_id: str, query: str | None = None):
    if query:
        return {"item_id": user_id, "query": query}
    return {"item_id": user_id}


@api.get("/users")
@crud.db_session
def get_users(current_user: Admin = Depends(get_current_user)):
    return crud.get_users()


@api.get('/get_info_by_user_id/{user_id:int}')
@crud.db_session
def get_info_about_user(user_id, current_user: Admin = Depends(get_current_user)):
    return crud.get_user_info(crud.User[user_id])


@api.get('/get_user_balance_by_id/{user_id:int}')
@crud.db_session
def get_user_balance_by_id(user_id, current_user: Admin = Depends(get_current_user)):
    crud.update_wallet_balance(crud.User[user_id].wallet)
    return crud.User[user_id].wallet.balance


@api.get('/user_by_tg_id/{tg_id:int}')
@crud.db_session
def get_user_by_tg_id(tg_id, current_user: Admin = Depends(get_current_user)):
    return crud.get_user_info(crud.get_user_by_tg_id(tg_id))


@api.get("/get_user_wallet/{user_id:int}")
@crud.db_session
def get_user_wallet(user_id, current_user: Admin = Depends(get_current_user)):
    return crud.get_wallet_info(crud.User[user_id].wallet)


@api.get('/get_total_balance')
@crud.db_session
def get_total_balance(current_user: Admin = Depends(get_current_user)):
    balance = 0.0
    crud.update_all_wallets()
    for user in crud.User.select()[:]:
        balance += user.wallet.balance
    return balance


@api.get("/get_user_transactions/{user_id:int}")
@crud.db_session
def get_user_transactions(user_id, current_user: Admin = Depends(get_current_user)):
    return crud.get_user_info(crud.User[user_id])


@api.post('/user/create')
def create_user(user: pydantic_models.UserToCreate, current_user: Admin = Depends(get_current_user)):
    return crud.create_user(tg_id=user.tg_ID,
                            nick=user.nick if user.nick else None).to_dict()


@api.post('/create_transaction/{user_id:int}')
@crud.db_session
def create_transaction(user_id, transaction: pydantic_models.CreateTransaction, current_user: Admin = Depends(get_current_user)):
    return crud.create_transaction(sender=crud.User[user_id],
                                   receiver_address=transaction.receiver_address,
                                   amount_btc_without_fee=transaction.amount_btc_without_fee)


@api.put('/user/{user_id}')
def update_user(user_id: int, user: pydantic_models.UserToUpdate = fastapi.Body(), current_user: Admin = Depends(get_current_user)):
    return crud.update_user(user).to_dict()


@api.delete('/user/{user_id}')
@crud.db_session
def delete_user(user_id: int = fastapi.Path(), current_user: Admin = Depends(get_current_user)):
    crud.get_user_by_id(user_id).delete()
    return True


@api.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@api.get("/users/me/", response_model=Admin)
async def read_users_me(current_user: Admin = Depends(get_current_user)):
    return current_user
