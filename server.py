import datetime
import logging
import os
import re
import calendar
import asyncio
import aioschedule

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot_actions import start_calendar, processing_calendar
from clients_db import WorkWithClientDB
from bot_actions import BotWatch
from weather_info import Weather
from GPIOControl import turning_on, check_status

logging.basicConfig(level=logging.WARNING)

token = os.getenv("tg_token")
my_id = os.getenv("my_id")
user_id = os.getenv("user_id")

storage = MemoryStorage()
bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)

cl_info = []

# is_right_phone_number = re.compile(r'^\+?[78][-\(]?\d{3}\)?-?\d{3}-?\d{2}-?\d{2}$')
is_profit_sum = re.compile(r'(d+)')


class ClAddForm(StatesGroup):
    name = State()
    # number = State()
    comment = State()

# class AddNote(StatesGroup):



def auth(func):
    """ Разрешения на пользование ботом """
    async def wrapper(message):
        if message['from']['id'] != my_id or message['from']['id'] != user_id:
            return await func(message)

    return wrapper


@auth
async def return_to_start_menu(message):
    kb = [
        [
            types.KeyboardButton(text="Вернуться в стартовое меню"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Для возврата в главное меню, нажмите кнопку внизу экрана", reply_markup=keyboard)


@auth
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """ Инлайн кнопки главного меню """
    keyboard = types.InlineKeyboardMarkup()
    if message['from']['id'] != my_id:
        server_button = types.InlineKeyboardButton(text="Меню работы с сервером", callback_data="server")
        keyboard.add(server_button)
    button_weather = types.InlineKeyboardButton(text="Погода", callback_data="weather")
    button_bd = types.InlineKeyboardButton(text="Клиенты", callback_data="clients")
    button_notes = types.InlineKeyboardButton(text="Заметки", callback_data="notes")
    keyboard.add(button_weather, button_bd, button_notes)
    await message.answer("Выберите из списка ниже, чтобы Вы хотели сделать:", reply_markup=keyboard)


@auth
async def working_with_server(message):
    """ Инлайн кнопки выбора действий с сервером """
    keyboard = types.InlineKeyboardMarkup()
    on_off_server = types.InlineKeyboardButton(text="Включить/выключить сервер", callback_data="turn_on_serv")
    check_status = types.InlineKeyboardButton(text="Проверить, запущен ли сервер", callback_data="check_status")
    stop_immediately = types.InlineKeyboardButton(text="Выключить принудительно", callback_data="stop_immediately")
    keyboard.add(on_off_server)
    keyboard.add(check_status)
    keyboard.add(stop_immediately)
    await message.answer("Меню взаимодействия с сервером:", reply_markup=keyboard)


@auth
async def working_with_notes(message):
    """ Инлайн кнопки выбора действий с заметками """
    keyboard = types.InlineKeyboardMarkup()
    button_add_note = types.InlineKeyboardButton(text="Добавить заметку", callback_data="add_note")
    button_get_notes = types.InlineKeyboardButton(text="Просмотреть заметки", callback_data="get_notes")
    button_del_notes = types.InlineKeyboardButton(text="Удалить заметку", callback_data="del_note")
    keyboard.add(button_add_note)
    keyboard.add(button_get_notes)
    keyboard.add(button_del_notes)
    await message.answer("Выберите действие:", reply_markup=keyboard)


@auth
async def working_with_bd(message):
    """ Инлайн кнопки действий с БД """
    await return_to_start_menu(message)
    keyboard = types.InlineKeyboardMarkup()
    cl_list = types.InlineKeyboardButton(text="Список клиентов", callback_data="cl_list")
    app_list = types.InlineKeyboardButton(text="Записи", callback_data="app_list")
    add_client = types.InlineKeyboardButton(text="Добавить клиента", callback_data="add_client")
    statistics = types.InlineKeyboardButton(text="Статистика", callback_data="statistics")
    keyboard.add(cl_list)
    keyboard.add(app_list)
    keyboard.add(add_client)
    keyboard.add(statistics)
    await bot.send_message(message.chat.id, "Меню работы с БД:", reply_markup=keyboard)


async def working_with_clients(message, cl_id, cl_name):
    """ Инлайн кнопки действий с выбранным клиентом """
    keyboard = types.InlineKeyboardMarkup()
    cl_appoint = types.InlineKeyboardButton(text="Записать", callback_data=f"cl_appoint, {cl_id}, {cl_name}")
    change_cl_info = types.InlineKeyboardButton(text="Изменить данные", callback_data=f"change_cl_info, {cl_id}, {cl_name}")
    del_client = types.InlineKeyboardButton(text="Удалить клиента", callback_data=f"del_client, {cl_id}, {cl_name}")
    cancel_appoint = types.InlineKeyboardButton(text="Отменить запись", callback_data=f"cancel_appoint, {cl_id}, {cl_name}")
    add_profit = types.InlineKeyboardButton(text="Внести сумму", callback_data=f"add_profit, {cl_id}, {cl_name}")
    keyboard.add(cl_appoint)
    keyboard.add(change_cl_info)
    keyboard.add(del_client)
    keyboard.add(cancel_appoint)
    keyboard.add(add_profit)
    await bot.send_message(message.chat.id, "Меню действий с клиентами:", reply_markup=keyboard)


async def working_with_weather(message):
    keyboard = types.InlineKeyboardMarkup()
    weather_now = types.InlineKeyboardButton(text="Погода сейчас", callback_data="weather_now")
    weather_today = types.InlineKeyboardButton(text="Погода на день", callback_data="weather_today")
    weather_tomorrow = types.InlineKeyboardButton(text="Погода на завтра", callback_data="weather_tomorrow")
    weather_several_days = types.InlineKeyboardButton(text="Погода на несколько дней",
                                                      callback_data="weather_several_days")
    keyboard.add(weather_now)
    keyboard.add(weather_today)
    keyboard.add(weather_tomorrow)
    keyboard.add(weather_several_days)
    await bot.send_message(message.chat.id, "Меню погоды:", reply_markup=keyboard)


async def change_info_bttns(message):
    keyboard = types.InlineKeyboardMarkup()
    change_name = types.InlineKeyboardButton(text="Изменить имя", callback_data=f"ch_name")
    # change_phone = types.InlineKeyboardButton(text="Изменить телефон", callback_data=f"ch_phone")
    change_comment = types.InlineKeyboardButton(text="Изменить комментарий", callback_data=f"ch_comment")
    keyboard.add(change_name)
    # keyboard.add(change_phone)
    keyboard.add(change_comment)
    await bot.send_message(message.chat.id, "Выберите, что хотите изменить:", reply_markup=keyboard)


@auth
@dp.callback_query_handler(lambda call: call.data)
async def callback_worker(call, state: FSMContext):
    """ Хэндлеры инлайн кнопок """

    message = call.message

    if "," not in call.data:
        if call.data == "server":
            await working_with_server(message)
        elif call.data == "turn_on_serv":
            turn_on = turning_on(0.5)
            await bot.send_message(my_id, turn_on)
        elif call.data == "check_status":
            turn_on_imm = turning_on(4)
            await bot.send_message(my_id, turn_on_imm)
        elif call.data == "stop_immediately":
            await working_with_server(message)
        elif call.data == "weather":
            await working_with_weather(message)
        elif call.data == "weather_now":
            time, temp, feels_like, pressure, humidity, cloudy, wind, wind_dir, visibility = Weather.weather_now()
            weather = f"{time}\n{temp}\n{feels_like}\n{pressure}\n{humidity}\n{cloudy}\n{wind}\n{wind_dir}\n{visibility}"
            await bot.send_message(message.chat.id, weather)
        elif call.data == "weather_today":
            try:
                weather = Weather.weather_on_day(today=True)
                await bot.send_message(message.chat.id, "\n\n".join(weather))
            except Exception:
                await bot.send_message(message.chat.id, "На сегодня погоды уже нет")
        elif call.data == "weather_tomorrow":
            weather = Weather.weather_on_day()
            await bot.send_message(message.chat.id, "\n\n".join(weather))
        elif call.data == "weather_several_days":
            weather = Weather.weather_on_several()
            await bot.send_message(message.chat.id, weather)
        elif call.data == "clients":
            await working_with_bd(message)
        elif call.data == "notes":
            await working_with_notes(message)
        elif call.data == "get_notes":
            async with state.proxy() as data:
                data['cal_usage'] = 'get_note'
            await message.answer("Выберите дату: ", reply_markup=await start_calendar())
        elif call.data == "add_note":
            async with state.proxy() as data:
                data['cal_usage'] = 'add_note'
                data['act'] = 'note_time'
            await message.answer("Выберите дату: ", reply_markup=await start_calendar())
        elif call.data == "del_note":
            async with state.proxy() as data:
                data['cal_usage'] = 'del_note'
            await message.answer("Выберите дату: ", reply_markup=await start_calendar())
        elif call.data == "approve_del_note":
            async with state.proxy() as data:
                date = data['date']
                note = data['note']
            WorkWithClientDB.del_note(date, note)
            await bot.send_message(message.chat.id, "Заметка удалена")
            await state.finish()
            await send_welcome(message)
        elif call.data == "app_list":
            async with state.proxy() as data:
                data['cal_usage'] = 'get_app_list'
            await message.answer("Выберите дату: ", reply_markup=await start_calendar())
        elif call.data == "cl_list":
            await show_clients_list(message)
        elif call.data == "add_client":
            await bot.send_message(message.chat.id, "Введите имя клиента:")
            await ClAddForm.name.set()
        elif call.data == "statistics":
            string = WorkWithClientDB.get_statistics()
            await bot.send_message(message.chat.id, string)
            await send_welcome(message)
        elif call.data == "ch_name":
            await bot.send_message(message.chat.id, "Введите новое имя:")
            async with state.proxy() as data:
                data['result'] = 'change_name'
        # elif call.data == "ch_phone":
        #     await bot.send_message(message.chat.id, "Введите новый телефон:")
        #     async with state.proxy() as data:
        #         data['result'] = 'change_phone'
        elif call.data == "ch_comment":
            await bot.send_message(message.chat.id, "Введите новый комментарий:")
            async with state.proxy() as data:
                data['result'] = 'change_comment'
        elif call.data == 'approve_del_client':
            async with state.proxy() as data:
                cl_id = data['cl_id']
                cl_name = data['cl_name']
            WorkWithClientDB.del_client(cl_id)
            await bot.send_message(message.chat.id, f"Клиент{cl_name} удалён!")
            await state.finish()
            await send_welcome(message)
        elif call.data == 'approve_cancel_appoint':
            async with state.proxy() as data:
                cl_id = data['cl_id']
                cl_name = data['cl_name']
            WorkWithClientDB.cancel_appointment(cl_id)
            await bot.send_message(message.chat.id, f"Запись клиента{cl_name} отменена!")
            await state.finish()
            await send_welcome(message)

    else:
        act, cl_id, cl_name = call.data.split(",")
        async with state.proxy() as data:
            data['cl_id'] = cl_id
            data['cl_name'] = cl_name
        if act == "cl_appoint":
            async with state.proxy() as data:
                data['cal_usage'] = 'appoint'
            await message.answer("Выберите дату: ", reply_markup=await start_calendar())
        elif act == "change_cl_info":
            await change_info_bttns(message)
        elif act == "del_client":
            keyboard = types.InlineKeyboardMarkup()
            del_cl = types.InlineKeyboardButton(text="Удалить", callback_data="approve_del_client")
            keyboard.add(del_cl)
            await bot.send_message(message.chat.id, f"Вы действительно хотите удалить клиента{cl_name}?",
                                   reply_markup=keyboard)
        elif act == "cancel_appoint":
            async with state.proxy() as data:
                cl_id = int(data['cl_id'])
            result = WorkWithClientDB.show_appointment_info_by_cl_id(cl_id)
            if len(result) != 0:
                date_lst = []
                for info in result:
                    name, app_date, app_comment, _ = info
                    date_lst.append(datetime.datetime.strptime(f"{app_date}", "%d-%m-%Y %H:%M:%S"))
                app_date = datetime.datetime.strftime(max(date_lst), "%d-%m-%Y %H:%M:%S")
                day, time = app_date.split(" ")
                await bot.send_message(message.chat.id, f"Клиент {name} записан на {day} в {time}")
                keyboard = types.InlineKeyboardMarkup()
                cancel_cl_app = types.InlineKeyboardButton(text="Отменить", callback_data="approve_cancel_appoint")
                keyboard.add(cancel_cl_app)
                await bot.send_message(message.chat.id, f"Вы действительно хотите отменить запись?",
                                       reply_markup=keyboard)
            else:
                await bot.send_message(message.chat.id, f"Данный клиент ещё не был записан!")
        elif act == "add_profit":
            date_lst = []
            result = WorkWithClientDB.show_appointment_info_by_cl_id(cl_id)
            for info in result:
                name, app_date, app_comment, _ = info
                date = datetime.datetime.strptime(f"{app_date}", "%d-%m-%Y %H:%M:%S")
                if date < datetime.datetime.now():
                    date_lst.append(date)
            if len(date_lst) == 0:
                await bot.send_message(message.chat.id, f"Клиент{cl_name} не был ранее записан!")
            else:
                app_date = datetime.datetime.strftime(max(date_lst), "%d-%m-%Y %H:%M:%S")
                async with state.proxy() as data:
                    data['app_date'] = app_date
                    data['result'] = 'add_profit'
                day, time = app_date.split(" ")
                await bot.send_message(message.chat.id, f"Клиент{cl_name} был записан на {day} в {time}")
                await bot.send_message(message.chat.id, f"Укажите сумму оплаты:")

    if "simple_calendar" in call.data:
        act = call.data.replace("simple_calendar", "")
        async with state.proxy() as data:
            data['act'] = act
        await processing_calendar(message, state, bot)

    if "continue" in call.data:
        watch = BotWatch(state, bot)
        async with state.proxy() as data:
            if data['act'] == 'app_time':
                text = 'Выберите время: '
            elif data['act'] == 'note_time':
                text = 'Выберите время, но если время для заметки не требуется - пропустите данный шаг,' \
                       'оставив в поле ноли'
        await message.answer(text, reply_markup=await watch.start_watch())

    if "watch" in call.data:
        act = call.data.lstrip("watch:")
        watch = BotWatch(state, bot)
        await watch.processing_watch(message, act)


@auth
async def show_clients_list(message):
    """ Функция показывающая список клиентов """
    cl_list = WorkWithClientDB.show_clients_list()
    result = []
    for info in cl_list:
        cl_id, name, comment = info
        string = f"/{cl_id}   {name}    {comment}\n"
        result.append(string)
    cl_lst = "".join(result)
    await bot.send_message(message.chat.id, cl_lst)


@auth
@dp.message_handler(regexp=r'(\d+)')
async def act_with_cl(message, state):
    """ Функция отлавливающая выбор клиента из списка по ID """
    async with state.proxy() as data:
        if 'result' in data.keys() and data['result'] == "del_note":
            note_num = str(message.text)
            notes = data['notes']
            note_lst = notes.split("\n")
            for item in note_lst:
                if note_num in item:
                    note = item.split('~')[1]
                    data['note'] = note
                    break
            keyboard = types.InlineKeyboardMarkup()
            appoint = types.InlineKeyboardButton(text="Да", callback_data=f"approve_del_note")
            keyboard.add(appoint)
            await bot.send_message(message.chat.id, f"Вы действительно хотите удалить заметку '{note}'?\n"
                                                    f"Для отмены действия просто вернитесь в начальное меню",
                                   reply_markup=keyboard)
        elif 'result' in data.keys():
            cl_id = data['cl_id']
            cl_name = data['cl_name']

            # if is_right_phone_number.match(message.text):
            #     phone_num = str(message.text)
            #     if data['result'] == 'change_phone':
            #         field = "phone"
            #         WorkWithClientDB.change_client_info(field, phone_num, cl_id)
            #         await bot.send_message(message.chat.id, f"Изменён номер телефона клиента{cl_name} на {phone_num}")
            #         await state.finish()
            #         await send_welcome(message)

            if "/" not in message.text:
                profit = int(message.text)
                date = data['app_date']
                WorkWithClientDB.add_profit(profit, cl_id, date)
                await bot.send_message(message.chat.id, f"Внесена сумма {profit} за клиента{cl_name}. Дата: {date}")
                await state.finish()
                await send_welcome(message)

        else:
            cl_id = int(str(message.text).strip("/"))
            cl_name = WorkWithClientDB.show_client_info(cl_id)[1]
            async with state.proxy() as data:
                data['cl_id'] = cl_id
                data['cl_name'] = cl_name
            await bot.send_message(message.chat.id, f"Выбран клиент '{cl_name}'")
            await working_with_clients(message, cl_id, cl_name)


@dp.message_handler(Text(equals='Вернуться в стартовое меню'))
async def some_func(msg: types.Message, state):
    async with state.proxy() as data:
        if len(data.keys()) != 0:
            await state.finish()
    await send_welcome(msg)


@auth
@dp.message_handler(lambda message: message.text)
async def comment_add(message, state):
    """ Функция добавления комментария к записи """
    comment = message.text
    async with state.proxy() as data:

        if 'cl_id' in data.keys() and 'cl_name' in data.keys():
            cl_id = data['cl_id']
            cl_name = data['cl_name']

            if data['result'] == 'appointment':
                date = data['date']
                WorkWithClientDB.make_appointment(int(cl_id), date, comment)
                day, time = date.split(" ")
                await bot.send_message(message.chat.id, f"Клиент{cl_name} записан на {day} в {time}")
                await state.finish()
                await send_welcome(message)
            elif data['result'] == 'note_added':
                date = data['date']
                day, time = date.split(" ")
                WorkWithClientDB.add_note(date, comment)
                if time == '00:00:00':
                    text = f"Сохранена заметка на {day}"
                else:
                    text = f"Сохранена заметка на {day} в {time}"
                await bot.send_message(message.chat.id, text)
                await state.finish()
                await send_welcome(message)
            elif data['result'] == 'change_name':
                field = "name"
                WorkWithClientDB.change_client_info(field, comment, cl_id)
                await bot.send_message(message.chat.id, f"Имя клиента{cl_name} изменено на {comment}")
                await state.finish()
                await send_welcome(message)
            elif data['result'] == 'change_comment':
                field = "description"
                WorkWithClientDB.change_client_info(field, comment, cl_id)
                await bot.send_message(message.chat.id, f"Комментарий клиента{cl_name} изменен на {comment}")
                await state.finish()
                await send_welcome(message)

        elif 'date' in data.keys():
            date = data['date']
            if data['result'] == "note_added":
                WorkWithClientDB.add_note(date, comment)
                await bot.send_message(message.chat.id, f"Добавлена заметка на {date}")
                await state.finish()
                await send_welcome(message)

@auth
@dp.message_handler(state=ClAddForm.name) # Принимаем состояние
async def add_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data: # Устанавливаем состояние ожидания
        data['name'] = message.text
    await bot.send_message(message.chat.id, "Введите комментарий для клиента:")
    await ClAddForm.comment.set()


# @auth
# @dp.message_handler(state=ClAddForm.number) # Принимаем состояние
# async def add_phone(message: types.Message, state: FSMContext):
#     async with state.proxy() as data: # Устанавливаем состояние ожидания
#         if message.text == '':
#             data['number'] = message.text
#             await bot.send_message(message.chat.id, "Введите комментарий для клиента:")
#             await ClAddForm.comment.set()
#         elif is_right_phone_number.match(message.text):
#             data['number'] = message.text
#             await bot.send_message(message.chat.id, "Введите комментарий для клиента:")
#             await ClAddForm.comment.set()
#         else:
#             await bot.send_message(message.chat.id, "Введите номер телефона корректно!")
#             await ClAddForm.number.set()


@auth
@dp.message_handler(state=ClAddForm.comment) # Принимаем состояние
async def add_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data: # Устанавливаем состояние ожидания
        name = data['name']
        # number = data['number']
    comment = message.text

    if comment == 'Вернуться в стартовое меню':
        await bot.send_message(message.chat.id, f"Сохранение нового клиента отменено!")

    else:
        WorkWithClientDB.client_create(name, comment)
        await bot.send_message(message.chat.id, f"Сохранён новый клиент:\nИмя: {name}\n"
                                                f"Комментарий: {comment}")
    await state.finish()
    await send_welcome(message)


def get_month_range(start_date=None):
    if start_date is None:
        two_month_ago = int(datetime.date.today().month) - 2
        start_date = datetime.date.today().replace(month=two_month_ago).replace(day=1)
    _, days_in_month = calendar.monthrange(start_date.year, start_date.month)
    end_date = start_date + datetime.timedelta(days=days_in_month)
    return start_date, end_date


def get_year_range():
    month_list = []
    for i in range(1, 13):
        year_ago = int(datetime.date.today().year) - 1
        start_date = datetime.date.today().replace(year=year_ago).replace(month=i).replace(day=1)
        _, days_in_month = calendar.monthrange(start_date.year, start_date.month)
        end_date = start_date + datetime.timedelta(days=days_in_month)
        month_list.append((start_date, end_date))
    return month_list


async def cleaner():
    year_now = datetime.date.today().year
    month_days = []
    a_day = datetime.timedelta(days=1)
    first_day, last_day = get_month_range()
    while first_day < last_day:
        month_days.append(datetime.datetime.strftime(first_day, "%d-%m-%Y"))
        first_day += a_day
    tuple_month_lst = tuple(month_days)
    cnt = WorkWithClientDB.get_notes_for_month(tuple_month_lst)
    try:
        if len(cnt) != 0:
            WorkWithClientDB.db_cleaner(tuple_month_lst)
            month = month_days[0].split("-")[1]
            await bot.send_message(my_id, f"Произведена очистка БД от старых заметок за {month} месяц")
    except Exception as e:
        await bot.send_message(my_id, f"Возникла ошибка при очистке БД от старых заметок: {e}")

    year_days = []
    if datetime.datetime.strftime(datetime.datetime.today(), "%d-%m-%Y") == f'10-01-{year_now}':
        for month in get_year_range():
            first_day, last_day = month
            while first_day < last_day:
                year_days.append(datetime.date.strftime(first_day, "%d-%m-%Y"))
                first_day += a_day
        tuple_year_lst = tuple(year_days)
        cnt = WorkWithClientDB.check_appointment(tuple_year_lst)
        try:
            if len(cnt) != 0:
                WorkWithClientDB.db_appointment_cleaner(tuple_year_lst)
                year = int(year_now) - 1
                await bot.send_message(my_id, f"Произведена очистка БД от старых записей за {year} месяц")
        except Exception as e:
            await bot.send_message(my_id, f"Возникла ошибка при очистке БД от старых записей: {e}")


async def reminder():
    today = datetime.date.strftime(datetime.datetime.today(), "%d-%m-%Y")
    tomorrow = datetime.date.strftime((datetime.datetime.today() + datetime.timedelta(days=1)), "%d-%m-%Y")
    after_tomorrow = datetime.date.strftime((datetime.datetime.today() + datetime.timedelta(days=2)), "%d-%m-%Y")
    today_notes = WorkWithClientDB.get_notes_for_month(today)
    tommorrow_notes = WorkWithClientDB.get_notes_for_month(tomorrow)
    after_tomorrow_notes = WorkWithClientDB.get_notes_for_month(after_tomorrow)
    today_app = WorkWithClientDB.show_appointment_info_by_date(f"{today}%")
    tomorrow_app = WorkWithClientDB.show_appointment_info_by_date(f"{tomorrow}%")
    after_tomorrow_app = WorkWithClientDB.show_appointment_info_by_date(f"{after_tomorrow}%")

    if len(today_notes) != 0:
        today_notes_join = "\n".join([i[0] for i in today_notes])
        today_notes_str = f"Заметки на сегодня:\n{today_notes_join}"
    else:
        today_notes_str = f"Заметок на сегодня нет"

    if len(tommorrow_notes) != 0:
        tomorrow_notes_join = "\n".join([i[0] for i in tommorrow_notes])
        tomorrow_notes_str = f"Заметки на завтра:\n{tomorrow_notes_join}"
    else:
        tomorrow_notes_str = f"Заметок на завтра нет"

    if len(after_tomorrow_notes) != 0:
        after_tomorrow_notes_join = "\n".join([i[0] for i in after_tomorrow_notes])
        after_tomorrow_notes_str = f"Заметки на послезавтра:\n{after_tomorrow_notes_join}"
    else:
        after_tomorrow_notes_str = f"Заметок на послезавтра нет"

    if len(today_app) != 0:
        today_app_join = "\n".join([f"{i[2]} {i[1]}" for i in today_app])
        today_app_str = f"Записаны на сегодня:\n{today_app_join}"
    else:
        today_app_str = f"Записей на сегодня нет"

    if len(tomorrow_app) != 0:
        tomorrow_app_join = "\n".join([f"{i[2]} {i[1]}" for i in tomorrow_app])
        tomorrow_app_str = f"Записаны на завтра:\n{tomorrow_app_join}"
    else:
        tomorrow_app_str = f"Записей на завтра нет"

    if len(after_tomorrow_app) != 0:
        after_tomorrow_app_join = "\n".join([f"{i[2]} {i[1]}" for i in after_tomorrow_app])
        after_tomorrow_app_str = f"Записаны на послезавтра:\n{after_tomorrow_app_join}"
    else:
        after_tomorrow_app_str = f"Записей на послезавтра нет"

    await bot.send_message(user_id, f"{today_notes_str}\n\n{tomorrow_notes_str}\n\n{after_tomorrow_notes_str}"
                                    f"\n\n{today_app_str}\n\n{tomorrow_app_str}\n\n{after_tomorrow_app_str}")


async def reminder_note():
    now = datetime.date.strftime(datetime.datetime.now(), "%d-%m-%Y %H:%M")
    note = WorkWithClientDB.get_note_now(now.rstrip(":00"))
    try:
        if len(note) != 0:
            await bot.send_message(user_id, f"Напоминание: {note[0]}")
    except TypeError:
        pass


async def scheduler():
    aioschedule.every().sunday.at("23:00").do(cleaner)
    aioschedule.every().day.at("12:00").do(reminder)
    aioschedule.every().minute.do(reminder_note)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(2)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
