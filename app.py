import fastapi
import pydantic_models
import database.crud as crud
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic_models import UserToValidate

api = fastapi.FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
def get_users():
    return crud.get_users()


@api.get('/get_info_by_user_id/{user_id:int}')
@crud.db_session
def get_info_about_user(user_id):
    return crud.get_user_info(crud.User[user_id])


@api.get('/get_user_balance_by_id/{user_id:int}')
@crud.db_session
def get_user_balance_by_id(user_id):
    crud.update_wallet_balance(crud.User[user_id].wallet)
    return crud.User[user_id].wallet.balance


@api.get('/user_by_tg_id/{tg_id:int}')
@crud.db_session
def get_user_by_tg_id(tg_id: int):
    return crud.get_user_info(crud.get_user_by_tg_id(tg_id))


@api.get("/get_user_wallet/{user_id:int}")
@crud.db_session
def get_user_wallet(user_id):
    return crud.get_wallet_info(crud.User[user_id].wallet)


@api.get('/get_total_balance')
@crud.db_session
def get_total_balance():
    balance = 0.0
    crud.update_all_wallets()
    for user in crud.User.select()[:]:
        balance += user.wallet.balance
    return balance


@api.get("/get_user_transactions/{user_id:int}")
@crud.db_session
def get_user_transactions(user_id):
    return crud.get_user_info(crud.User[user_id])


@api.post('/user/create')
def create_user(user: pydantic_models.UserToCreate):
    return crud.create_user(tg_id=user.tg_ID,
                            nick=user.nick if user.nick else None).to_dict()


@api.post('/create_transaction/{user_id:int}')
@crud.db_session
def create_transaction(transaction: pydantic_models.CreateTransaction, user_id: int = fastapi.Path()):
    return crud.create_transaction(sender=crud.User[user_id],
                                   receiver_address=transaction.receiver_address,
                                   amount_btc_without_fee=transaction.amount_btc_without_fee)


@api.put('/user/{user_id}')
def update_user(user_id: int, user: pydantic_models.UserToUpdate = fastapi.Body()):
    return crud.update_user(user).to_dict()


@api.delete('/user/{user_id}')
@crud.db_session
def delete_user(user_id: int = fastapi.Path()):
    crud.get_user_by_id(user_id).delete()
    return True


def fake_decode_token(token):
    return UserToValidate(username=token + "fakedecoded",
                          email="john@example.com",
                          full_name="John Doe")


async def get_current_user(token: str = fastapi.Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    return user


@api.get("/users/me")
async def read_users_me(current_user: UserToValidate = fastapi.Depends(get_current_user)):
    return current_user
