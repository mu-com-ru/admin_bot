from database import Message, Priority, Soft, SessionLocal
from aiogram import Bot, Dispatcher, executor, types
from utils import Guide, spam_protect
from aiogram.utils.exceptions import ChatNotFound
from sqlalchemy import Date, cast
import datetime
import asyncio
import logging
import conf


logging.basicConfig(level=logging.INFO)
bot = Bot(token=conf.TOKEN)
dp = Dispatcher(bot)


class SendMessage:
    @staticmethod
    def alert_format(data):
        def func(x):
            return f'[{x[1]}] {x[0]}'
        return '\n'.join(map(func, data))

    @classmethod
    def split_message(cls, data):
        str_len = len(data)
        count_mes = str_len // ((str_len // 4100) + 1)
        return [data[i:i+count_mes] for i in range(0, str_len, count_mes)]

    @classmethod
    async def admin_alert(cls, data):
        queue = cls.split_message(cls.alert_format(data))
        print(data)
        for id in conf.admin_id:
            try:
                for elem in queue:
                    await bot.send_message(id, elem)
            except ChatNotFound as e:
                print(e)

    @classmethod
    async def split_answer(cls, data: str, message: types.Message):
        queue = cls.split_message(cls.alert_format(data))
        for elem in queue:
            await message.answer(elem)


async def check_base():
    try:
        connect = Connection()
        while Guide.task is not None:
            query_data = connect.db.query(Message).filter_by(
                    priority=2, complete=0)
            data = query_data.join(
                Message.soft_fk).add_entity(Soft).from_self().all()
            if data:
                await SendMessage.admin_alert(data)
                query_data.update({'complete': 1})
                connect.db.commit()
            await asyncio.sleep(10)
    except Exception as e:
        print(e, type(e))


def get_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start = types.KeyboardButton('/start')
    stop = types.KeyboardButton('/stop')
    today = types.KeyboardButton('/today')
    priority_1 = types.KeyboardButton('/priority 1')
    priority_2 = types.KeyboardButton('/priority 2')
    priority_3 = types.KeyboardButton('/priority 3')
    help = types.KeyboardButton('/help')
    all = types.KeyboardButton('/all')
    kb.add(start, stop, today, priority_1, priority_2, priority_3, help, all)
    return kb


class Connection:
    connect = None

    def __init__(self):
        if Connection.connect is None:
            self.db = SessionLocal()
            Connection.connect = self.db
            print('Open connection')
        else:
            self.db = Connection.connect

    def __del__(self):
        Connection.connect = None
        self.db.close()
        print('Close connextion')





@dp.message_handler(commands=['start'])
@spam_protect
async def start_check(message: types.Message):
    if Guide.task is not None:
        await message.answer('Уже работаю')
        return
    Guide.task = asyncio.ensure_future(check_base())
    print('Работаю!')
    kb = get_kb()
    await message.answer('Работаю!', reply_markup=kb)


@dp.message_handler(commands=['stop'])
async def stop_check(message: types.Message):
    if Guide.task is not None:
        Guide.task.cancel()
        Guide.task = None
        print('Встал!')
        await message.answer('Встал!')
    else:
        await message.answer('Давненько стою!')


@dp.message_handler(commands=['today'])
@spam_protect
async def today_message(message: types.Message):
    try:
        connect = Connection()
        data = connect.db.query(Message).join(Message.soft_fk).add_entity(
            Soft).from_self().filter(
                cast(Message.created,
                Date) == datetime.datetime.today().date()).all()
        if data:
            await SendMessage.split_answer(data, message)
        else:
            await message.answer('Нет сообщений')
    except Exception as e:
        await message.answer(f'Ошибка {e} {type(e)}')

@dp.message_handler(commands=['priority'])
@spam_protect
async def priority_message(message: types.Message):
    try:
        connect = Connection()
        priority = message.text.split()[1]
        query_data = connect.db.query(Message).join(
            Message.soft_fk).add_entity(Soft).from_self().filter_by(
                priority=priority, complete=0)
        data = query_data.all()
        if data:
            await SendMessage.split_answer(data, message)
            connect.db.query(Message).filter_by(
                priority=priority, complete=0).update({'complete': 1})
            connect.db.commit()
        else:
            await message.answer("Нет сообщений")
    except Exception as e:
        await message.answer(f'Ошибка {e} {type(e)}')


@dp.message_handler(commands=['all'])
@spam_protect
async def all_incomplete(message: types.Message):
    try:
        connect = Connection()
        data = connect.db.query(Message).join(Message.soft_fk).add_entity(
            Soft).from_self().filter_by(complete=0).all()
        if data:
            await SendMessage.split_answer(data, message)
        else:
            await message.answer("Нет сообщений")
    except Exception as e:
        await message.answer(f'Ошибка {e} {type(e)}')


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.answer('Commands: start stop today priority(0 1 2)')


@dp.message_handler()
async def wtf(message: types.Message):
    print(message.text)
    await message.answer('Нет такой команды')


if __name__ == '__main__':
    executor.start_polling(dp)
