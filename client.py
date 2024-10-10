import asyncio

import aiohttp


async def main():

    # session = aiohttp.ClientSession()
    # response = await session.post("http://127.0.0.1:8080/user/",
    #                              json={"name": "user_5", "password": "1234"}
    #                              )
    # print(response.status)
    # print(await response.text())
    session = aiohttp.ClientSession()

    # response = await session.patch("http://127.0.0.1:8080/user/8",
    #                              json={"name": "new_name_1"})
    #
    # print(response.status)
    # print(await response.text())

    response = await session.delete(
        "http://127.0.0.1:8080/user/8",
    )
    print(response.status)
    print(await response.text())

    response = await session.get(
        "http://127.0.0.1:8080/user/8",
    )
    print(response.status)
    print(await response.text())

    await session.close()


asyncio.run(main())
