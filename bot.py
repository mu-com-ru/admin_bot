from aiogram import Bot, Dispatcher, executor, types
from database import Message, Priority, Soft, SessionLocal
from sqlalchemy import Date, cast
import logging
import conf
import asyncio
import datetime


logging.basicConfig(level=logging.INFO)
bot = Bot(token=conf.TOKEN)
dp = Dispatcher(bot)
check_event = False


async def admin_alert(data):
    data = '\n'.join(map(str, data))
    for id in conf.admin_id:
        await bot.send_message(id, data)


async def check_base():
    global check_event
    while check_event:
        connect = Connection()
        query_data = connect.db.query(
            Message).filter_by(priority=2, complete=0)
        data = query_data.all()
        if data:
            await admin_alert(data)
            query_data.update({'complete': 1})
            connect.db.commit()
        del connect
        await asyncio.sleep(60)


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
    def __init__(self):
        self.db = SessionLocal()
        print('Open connection')

    def __del__(self):
        self.db.close()
        print('Close connextion')


async def split_answer(data: str, message: types.Message):
    data = '\n'.join(map(str, data))
    str_len = len(data)
    count_mes =  str_len // ((str_len // 4100) + 1)
    print(data, str_len, count_mes)
    queue = [data[i:i+count_mes] for i in range(0, str_len, count_mes)]
    for elem in queue:
        await message.answer(elem)


@dp.message_handler(commands=['start'])
async def start_check(message: types.Message):
    global check_event
    if check_event:
        await message.answer('Уже работаю')
        return
    check_event = True
    print('Работаю!')
    asyncio.create_task(check_base())
    kb = get_kb()
    await message.answer('Работаю!', reply_markup=kb)


@dp.message_handler(commands=['stop'])
async def stop_check(message: types.Message):
    global check_event
    if check_event:
        check_event = False
        print('Встал!')
        await message.answer('Встал!')
    else:
        await message.answer('Давненько стою!')


@dp.message_handler(commands=['today'])
async def today_message(message: types.Message):
    connect = Connection()
    data = connect.db.query(Message).filter(
        cast(Message.created, Date) == datetime.datetime.today().date()).all()
    if data:
        await split_answer(data, message)
    else:
        await message.answer('Нет сообщений')


@dp.message_handler(commands=['priority'])
async def priority_message(message: types.Message):
    try:
        connect = Connection()
        priority = message.text.split()[1]
        query_data = connect.db.query(Message).filter_by(
            priority=priority, complete=0)
        data = query_data.all()
        if data:
            await split_answer(data, message)
            query_data.update({'complete': 1})
            connect.db.commit()
        else:
            await message.answer("Нет сообщений")
    except Exception as e:
        await message.answer('Ошибка ' + str(e))


@dp.message_handler(commands=['all'])
async def all_incomplete(message: types.Message):
    try:
        connect = Connection()
        data = connect.db.query(Message).filter_by(complete=0).all()
        if data:
            await split_answer(data, message)
        else:
            await message.answer("Нет сообщений")
    except Exception as e:
        await message.answer("Ошибка " + str(e))


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.answer('Commands: start stop today priority(0 1 2)')


@dp.message_handler()
async def wtf(message: types.Message):
    print(message.text)
    await message.answer('Нет такой команды')


if __name__ == '__main__':
    executor.start_polling(dp)
