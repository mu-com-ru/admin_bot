from aiogram import Bot, Dispatcher, executor, types
import logging
import psycopg2
import conf
import asyncio
import datetime

logging.basicConfig(level=logging.INFO)

bot = Bot(token=conf.TOKEN)
dp = Dispatcher(bot)

check_event = False
connect = None
cursor = None


def get_con_cur():
    global connect, cursor
    connect = psycopg2.connect(dbname=conf.DATABASES['NAME'],
                                user=conf.DATABASES['USER'],
                                password=conf.DATABASES['PASSWORD'],
                                host=conf.DATABASES['HOST'],
                                port = conf.DATABASES['PORT'])
    cursor = connect.cursor()


def send_request(request):
    global connect, cursor
    cursor.execute(request)
    try:
        data = cursor.fetchall()
    except:
        data = None
    connect.commit()
    return data


def close_con_cur():
    global connect, cursor
    cursor.close()
    connect.close()


def output_format(data):
    output = ''
    for i in data:
        output += ' '.join(i) + '\n'
    return output


async def admin_alert(data):
    for i in data[0]:
        print(type(i))
    for i in data:
        print(conf.requests['alert_complite'] + str(i[0]))
        send_request(conf.requests['alert_complite'] + str(i[0]))
        for j in conf.admin_id:
            await bot.send_message(j, i)


async def check_base():
    global check_event, connect, cursor
    while check_event:
        get_con_cur()
        data = send_request(conf.requests['get_data_alert'])
        if data:
            await admin_alert(data)
        print(data)
        close_con_cur()
        await asyncio.sleep(60)


@dp.message_handler(commands=['start'])
async def start_check(message: types.Message):
    global check_event
    if check_event:
        await message.answer('Уже работаю')
        return
    check_event = True
    print('Работаю!')
    await message.answer('Работаю!')
    await check_base()


@dp.message_handler(commands=['stop'])
async def stop_check(message: types.Message):
    global check_event
    check_event = False
    print('Встал!')
    await message.answer('Встал!')


@dp.message_handler(commands=['today'])
async def today_message(message: types.Message):
    get_con_cur()
    data = send_request(conf.requests['alert_today'] + "'" + str(datetime.datetime.today().date()) + "'")
    if data:
        await message.answer(output_format(data))
    else:
        await message.answer('Нет сообщений')
    close_con_cur()


@dp.message_handler(commands=['priority'])
async def priority_message(message: types.Message):
    get_con_cur()
    try:
        priority = message.text.split()[1]
        data = send_request(conf.requests['alert_priority'] + priority)
        if data:
            await message.answer(output_format(data))
            for i in data:
                send_request(conf.requests['alert_complite'] + str(i[0]))
        else:
            await message.answer("Нет сообщений")
    except Exception as e:
        await message.answer('Ошибка ' + str(e))
    close_con_cur()


@dp.message_handler(commands=['all'])
async def all_incomplete(message: types.Message):
    get_con_cur()
    try:
        data = send_request(conf.requests['all_incomplete'])
        if data:
            await message.answer(output_format(data))
            for i in data:
                send_request(conf.requests['alert_complite'] + str(i[0]))
        else:
            await message.answer("Нет сообщений")
    except Exception as e:
        await message.answer("Ошибка " + str(e))


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
	message.answer('Commands: start stop today priority(0 1 2)')
    

@dp.message_handler()
async def wtf(message: types.Message):
    print(message.text)
    await message.answer('Нет такой команды')

if __name__ == '__main__':
    executor.start_polling(dp)

# cursor.execute("INSERT INTO message (text_mess, soft_id, priority, complete) VALUES ('авария', 1, 1,0)")
