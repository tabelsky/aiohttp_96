import json

import bcrypt
from aiohttp import web
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Session, User, close_orm, init_orm


def hash_password(user_password: str) -> str:
    user_password = user_password.encode()
    hashed_password = bcrypt.hashpw(user_password, bcrypt.gensalt())
    hashed_password = hashed_password.decode()
    return hashed_password


def check_password(user_password: str, hashed_password: str):
    user_password = user_password.encode()
    hashed_password = hashed_password.encode()
    return bcrypt.checkpw(user_password, hashed_password)


app = web.Application()


async def orm_context(app):
    print("START")
    await init_orm()
    yield
    await close_orm()
    print("FINISH")


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        print(".....")
        return response


app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


def get_http_error(error_cls, error_msg):
    error = error_cls(
        text=json.dumps(
            {
                "error": error_msg,
            },
        ),
        content_type="application/json",
    )
    return error


async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise get_http_error(web.HTTPNotFound, "user not found")
    return user


async def add_user(session: AsyncSession, user: User):
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        raise get_http_error(web.HTTPConflict, "user already exist")
    return user


class UserView(web.View):

    @property
    def session(self) -> AsyncSession:
        return self.request.session

    @property
    def user_id(self):
        return int(self.request.match_info["user_id"])

    async def get(self):
        user = await get_user_by_id(self.session, self.user_id)
        return web.json_response(user.json)

    async def post(self):
        json_data = await self.request.json()
        json_data["password"] = hash_password(json_data["password"])
        user = User(**json_data)
        user = await add_user(self.session, user)
        return web.json_response({"id": user.id})

    async def patch(self):
        json_data = await self.request.json()
        if "password" in json_data:
            json_data["password"] = hash_password(json_data["password"])
        user = await get_user_by_id(self.session, self.user_id)
        for field, value in json_data.items():
            setattr(user, field, value)
        user = await add_user(self.session, user)
        return web.json_response({"id": user.id})

    async def delete(self):
        user = await get_user_by_id(self.session, self.user_id)
        await self.session.delete(user)
        await self.session.commit()
        return web.json_response({"status": "deleted"})


app.add_routes(
    [
        web.get("/user/{user_id:\d+}", UserView),
        web.patch("/user/{user_id:\d+}", UserView),
        web.delete("/user/{user_id:\d+}", UserView),
        web.post("/user/", UserView),
    ]
)

web.run_app(app)
