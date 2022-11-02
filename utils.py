import asyncio


class Guide:
    task = None
    __users_connect = []

    @classmethod
    def add(cls, id):
        cls.__users_connect.append(id)

    @classmethod
    def remove(cls, id):
        cls.__users_connect.remove(id)
    
    @classmethod
    def contains_id(cls, id):
        return id in cls.__users_connect


def alert_format(data):
    def func(x):
        return f'[{x[1]}] {x[0]}'
    return '\n'.join(map(func, data))


def spam_protect(func):
    async def protect(*args):
        if not Guide.contains_id(args[0].chat.id):
            print(args[0].chat.id)
            Guide.add(args[0].chat.id)
            await func(args[0])
            await asyncio.sleep(0.5)
            Guide.remove(args[0].chat.id)
    return protect
