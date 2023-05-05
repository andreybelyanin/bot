import calendar
from datetime import datetime, timedelta

from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

from clients_db import WorkWithClientDB

start_kb = ReplyKeyboardMarkup(resize_keyboard=True)

calendar_callback = CallbackData('simple_calendar', 'act', 'year', 'month', 'day')
watch_callback = CallbackData('watch', 'act', 'hours', 'minutes', 'seconds')

month_dict = {"January": "Январь", "February": "Февраль", "March": "Март",
              "April": "Апрель", "May": "Май", "June": "Июнь",
              "July": "Июль", "August": "Август", "September": "Сентябрь",
              "October": "Октябрь", "November": "Ноябрь", "December": "Декабрь"}


async def start_calendar(
        year: int = datetime.now().year,
        month: int = datetime.now().month
) -> InlineKeyboardMarkup:
    """ Функция инициализирующая календарь """
    inline_kb = InlineKeyboardMarkup(row_width=7)
    ignore_callback = calendar_callback.new("IGNORE", year, month, 0)  # for buttons with no answer
    # First row - Month and Year
    inline_kb.row()
    inline_kb.insert(InlineKeyboardButton(
        "Пр. год",
        callback_data=calendar_callback.new("PREV-YEAR", year, month, 1)
    ))
    inline_kb.insert(InlineKeyboardButton(
        f'{month_dict[calendar.month_name[month]]} {str(year)}',
        callback_data=ignore_callback
    ))
    inline_kb.insert(InlineKeyboardButton(
        "Сл. год",
        callback_data=calendar_callback.new("NEXT-YEAR", year, month, 1)
    ))
    # Second row - Week Days
    inline_kb.row()
    for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        inline_kb.insert(InlineKeyboardButton(day, callback_data=ignore_callback))

    # Calendar rows - Days of month
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        inline_kb.row()
        for day in week:
            if day == 0:
                inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
                continue
            inline_kb.insert(InlineKeyboardButton(
                str(day), callback_data=calendar_callback.new("DAY", year, month, day)
            ))

    # Last row - Buttons
    inline_kb.row()
    inline_kb.insert(InlineKeyboardButton(
        "Пр. месяц", callback_data=calendar_callback.new("PREV-MONTH", year, month, day)
    ))
    inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
    inline_kb.insert(InlineKeyboardButton(
        "Сл. месяц", callback_data=calendar_callback.new("NEXT-MONTH", year, month, day)
    ))
    return inline_kb


async def processing_calendar(message, state, bot):
    """ Функция работы с календарём """
    return_data = (False, None)
    async with state.proxy() as data:
        cal_usage = data['cal_usage']
        data = data['act']
    _, act, year, month, day = data.split(":")
    temp_date = datetime(int(year), int(month), 1)
    # processing empty buttons, answering with no action
    if act == "IGNORE":
        await message.answer(cache_time=60)
    # user picked a day button, return date
    if act == "DAY":
        # await message.delete_reply_markup()  # removing inline keyboard
        return_data = True, datetime(int(year), int(month), int(day))
    # user navigates to previous year, editing message with new calendar
    if act == "PREV-YEAR":
        prev_date = datetime(int(year) - 1, int(month), 1)
        await message.edit_reply_markup(await start_calendar(int(prev_date.year), int(prev_date.month)))
    # user navigates to next year, editing message with new calendar
    if act == "NEXT-YEAR":
        next_date = datetime(int(year) + 1, int(month), 1)
        await message.edit_reply_markup(await start_calendar(int(next_date.year), int(next_date.month)))
    # user navigates to previous month, editing message with new calendar
    if act == "PREV-MONTH":
        prev_date = temp_date - timedelta(days=1)
        await message.edit_reply_markup(await start_calendar(int(prev_date.year), int(prev_date.month)))
    # user navigates to next month, editing message with new calendar
    if act == "NEXT-MONTH":
        next_date = temp_date + timedelta(days=31)
        await message.edit_reply_markup(await start_calendar(int(next_date.year), int(next_date.month)))
    # at some point user clicks DAY button, returning date
    selected, unformatted_date = return_data

    date = None
    if selected:
        date = str(datetime.strftime(datetime.strptime(f"{unformatted_date}", "%Y-%m-%d %H:%M:%S"), "%d-%m-%Y"))

    if cal_usage == 'appoint':
        today = datetime.today()
        try:
            if datetime.strptime(date, "%d-%m-%Y") >= today:
                date_info = WorkWithClientDB.show_appointment_info_by_date(f"{date}%")
                if len(date_info) == 0:
                    result = "На этот день ещё никто не записан!"
                else:
                    result = getting_app_result(date_info)

                form_date = unformatted_date.strftime("%d/%m/%Y")
                async with state.proxy() as data:
                    data['date'] = form_date
                    data['act'] = 'app_time'

                await message.answer(
                    f'Вы выбрали {form_date}\n\n{result}',
                    reply_markup=start_kb
                )
                await curr_cl_appoint(message, state, bot)
            else:
                await message.answer(
                    f'На этот день уже нельзя сделать запись!'
                )
        except AttributeError:
            pass

    elif cal_usage == 'get_app_list':
        if date is not None:
            date_info = WorkWithClientDB.show_appointment_info_by_date(f"{date}%")
            if len(date_info) == 0:
                notes = "На этот день записей нет!"
            else:
                notes = getting_app_result(date_info)
            await message.answer(
                f'Дата: {date}\n{notes}',
                reply_markup=start_kb
            )

    elif cal_usage == 'get_note':
        if date is not None:
            date_info = WorkWithClientDB.get_notes(f"{date}%")
            if len(date_info) == 0:
                notes = "На этот день заметок нет!"
            else:
                notes = getting_notes_result(date_info)
            await message.answer(
                f'Дата: {date}\n{notes}',
                reply_markup=start_kb
            )

    elif cal_usage == 'add_note':
        try:
            if date is not None:
                date_info = WorkWithClientDB.get_notes(f"{date}%")
                # if datetime.strptime(app_date, "%d-%m-%Y %H:%M:%S") > datetime.now():
                compare_date = datetime.strptime(date, "%d-%m-%Y") + timedelta(days=1)
                if compare_date >= datetime.today():
                    if len(date_info) == 0:
                        notes = "На этот день заметок нет!"
                    elif len(date_info) != 0:
                        notes = getting_notes_result(date_info)

                    form_date = unformatted_date.strftime("%d-%m-%Y")
                    async with state.proxy() as data:
                        data['date'] = form_date
                        data['act'] = "note_time"

                    await message.answer(
                        f'Дата: {date}\n{notes}',
                        reply_markup=start_kb
                    )
                    await note_confirm(message, state, bot)

                elif compare_date < datetime.today():

                    if len(date_info) == 0:
                        notes = "На этот день заметок не было!"
                    elif len(date_info) != 0:
                        notes = getting_notes_result(date_info)

                    form_date = unformatted_date.strftime("%d-%m-%Y")
                    async with state.proxy() as data:
                        data['date'] = form_date

                    await message.answer(
                        f'Дата: {date}\n{notes}',
                        reply_markup=start_kb
                    )
        except AttributeError:
            pass

    elif cal_usage == 'del_note':
        if date is not None:
            date_info = WorkWithClientDB.get_notes(f"{date}%")
            # if datetime.strptime(app_date, "%d-%m-%Y %H:%M:%S") > datetime.now():
            compare_date = datetime.strptime(date, "%d-%m-%Y")

            if len(date_info) == 0:
                notes = "На этот день заметок нет!"
            elif len(date_info) != 0:
                notes = getting_notes_del(date_info)

            form_date = unformatted_date.strftime("%d-%m-%Y")
            async with state.proxy() as data:
                data['date'] = form_date
                data['result'] = "del_note"
                data['notes'] = notes

            await message.answer(
                f'Дата: {date}\n{notes}',
                reply_markup=start_kb
            )


async def note_confirm(message, state, bot):
    async with state.proxy() as data:
        data['result'] = "add_note"
    keyboard = types.InlineKeyboardMarkup()
    appoint = types.InlineKeyboardButton(text="Продолжить", callback_data=f"continue_notes")
    keyboard.add(appoint)
    await bot.send_message(message.chat.id, f"Сохранить заметку на этот день или выбрать другой?",
                           reply_markup=keyboard)


async def curr_cl_appoint(message, state, bot):
    """ Инлайн кнопка подверждения выбора даты """
    async with state.proxy() as data:
        date = data['date']
        cl_id = data['cl_id']
        cl_name = data['cl_name']
    keyboard = types.InlineKeyboardMarkup()
    appoint = types.InlineKeyboardButton(text="Продолжить", callback_data=f"continue; {cl_id}; {cl_name}; {date}")
    keyboard.add(appoint)
    await bot.send_message(message.chat.id, f"Записать {cl_name} на этот день или выбрать другой?",
                           reply_markup=keyboard)


def getting_app_result(date_info):
    """ Функция выводящая список записанных клиентов на выбранную дату """
    app_list = []
    for appoint in date_info:
        app_date, comment, client, amount = appoint
        app_time = app_date.split(" ")[1]
        if comment is None and amount is None:
            string = f"{app_time} {client}"
        elif amount is None:
            string = f"{app_time} {client} {comment}"
        elif comment is None:
            string = f"{app_time} {client} {amount}р"
        else:
            string = f"{app_time} {client} {comment} {amount}р."
        app_list.append(string)

    if len(app_list) != 0:
        app_info = "\n\n".join(app_list)
        if datetime.strptime(app_date, "%d-%m-%Y %H:%M:%S") > datetime.now():
            result = f"На этот день записаны:\n{app_info}"
        else:
            result = f"В этот день были записаны:\n{app_info}"
    return result


def getting_notes_result(date_info):
    notes_list = []
    for info in date_info:
        notes_list.append(info[0])
    return "\n".join(notes_list)


def getting_notes_del(date_info):
    notes_list = []
    for num, info in enumerate(date_info):
        notes_list.append(f"/{num}~{info[0]}")
    return "\n".join(notes_list)


class BotWatch:
    """ Класс виджета часов """

    def __init__(self, state, bot):
        self.hours = '00'
        self.minutes = '00'
        self.seconds = '00'
        self.inline_kb = InlineKeyboardMarkup(row_width=5)
        self.state = state
        self.bot = bot

    async def start_watch(self):
        """ Инициализация виджета часов """
        ignore_callback = watch_callback.new("IGNORE", self.hours, self.minutes,
                                             self.seconds)  # for buttons with no answer
        # First row - Plus 1 hour/10 minutes/10 seconds
        self.inline_kb.row()
        self.inline_kb.insert(InlineKeyboardButton(
            "+1h",
            callback_data=watch_callback.new("PLUS_ONE_HOUR", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "+10m",
            callback_data=watch_callback.new("PLUS_TEN_MINUTES", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "+10s",
            callback_data=watch_callback.new("PLUS_TEN_SECONDS", self.hours, self.minutes, self.seconds)
        ))
        # Second row - Plus 6 hours/ 30 minutes/ 30 seconds
        self.inline_kb.row()
        self.inline_kb.insert(InlineKeyboardButton(
            "+6h",
            callback_data=watch_callback.new("PLUS_SIX_HOURS", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "+30m",
            callback_data=watch_callback.new("PLUS_THIRTY_MINUTES", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "+30s",
            callback_data=watch_callback.new("PLUS_THIRTY_SECONDS", self.hours, self.minutes, self.seconds)
        ))
        # Third row - watch
        self.inline_kb.row()
        self.inline_kb.insert(InlineKeyboardButton(
            f"{self.hours}",
            callback_data=watch_callback.new("HOURS", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            ":",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            f"{self.minutes}",
            callback_data=watch_callback.new("MINUTES", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            ":",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            f"{self.seconds}",
            callback_data=watch_callback.new("SECONDS", self.hours, self.minutes, self.seconds)
        ))
        # Forth row - Minus 6 hours/ 30 minutes/ 30 seconds
        self.inline_kb.row()
        self.inline_kb.insert(InlineKeyboardButton(
            "-6h",
            callback_data=watch_callback.new("MINUS_SIX_HOURS", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "-30m",
            callback_data=watch_callback.new("MINUS_THIRTY_MINUTES", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "-30s",
            callback_data=watch_callback.new("MINUS_THIRTY_SECONDS", self.hours, self.minutes, self.seconds)
        ))
        # Fifth row  - Minus 1 hour/ten minutes/ten seconds
        self.inline_kb.row()
        self.inline_kb.insert(InlineKeyboardButton(
            "-1h",
            callback_data=watch_callback.new("MINUS_ONE_HOUR", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "-10m",
            callback_data=watch_callback.new("MINUS_TEN_MINUTES", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            " ",
            callback_data=ignore_callback
        ))
        self.inline_kb.insert(InlineKeyboardButton(
            "-10s",
            callback_data=watch_callback.new("MINUS_TEN_SECONDS", self.hours, self.minutes, self.seconds)
        ))
        self.inline_kb.row()
        self.inline_kb.insert(InlineKeyboardButton(
            "Продолжить",
            callback_data=watch_callback.new("APPROVE", self.hours, self.minutes, self.seconds)
        ))
        return self.inline_kb

    async def processing_watch(self, message, raw_action):
        """ Функция работы с часами """
        act, hour, minute, second = raw_action.split(":")
        self.hours = int(hour)
        self.minutes = int(minute)
        self.seconds = int(second)
        if act == "PLUS_ONE_HOUR":
            if self.hours >= 23:
                self.hours -= 23
            else:
                self.hours += 1
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "PLUS_SIX_HOURS":
            if self.hours >= 18:
                self.hours -= 18
            else:
                self.hours += 6
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "MINUS_ONE_HOUR":
            if self.hours <= 0:
                self.hours += 23
            else:
                self.hours -= 1
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "MINUS_SIX_HOURS":
            if self.hours <= 6:
                self.hours += 18
            else:
                self.hours -= 6
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "PLUS_TEN_MINUTES":
            if self.minutes >= 50:
                self.minutes -= 50
            else:
                self.minutes += 10
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "PLUS_THIRTY_MINUTES":
            if self.minutes >= 30:
                self.minutes -= 30
            else:
                self.minutes += 30
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "MINUS_THIRTY_MINUTES":
            if self.minutes <= 29:
                self.minutes += 30
            else:
                self.minutes -= 30
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "MINUS_TEN_MINUTES":
            if self.minutes <= 9:
                self.minutes += 50
            else:
                self.minutes -= 10
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "PLUS_TEN_SECONDS":
            if self.seconds >= 50:
                self.seconds -= 50
            else:
                self.seconds += 10
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "PLUS_THIRTY_SECONDS":
            if self.seconds >= 30:
                self.seconds -= 30
            else:
                self.seconds += 30
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "MINUS_THIRTY_SECONDS":
            if self.seconds <= 29:
                self.seconds += 30
            else:
                self.seconds -= 30
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "MINUS_TEN_SECONDS":
            if self.seconds <= 9:
                self.seconds += 50
            else:
                self.seconds -= 10
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            await message.edit_reply_markup(await self.start_watch())
        if act == "APPROVE":
            self.hours, self.minutes, self.seconds = is_less_then_ten(self.hours, self.minutes, self.seconds)
            # await comment_adding(message, self.state)

            async with self.state.proxy() as data:
                if data['act'] == 'app_time':
                    await message.answer(
                        f'Время записи: {self.hours}:{self.minutes}:{self.seconds}',
                        reply_markup=self.inline_kb
                    )
                    await self.bot.send_message(message.chat.id, "Осталось оставить комментрий к записи:")
                    # async with self.state.proxy() as data:
                    app_day = data['date'].replace("/", "-")
                    data['date'] = f"{app_day} {self.hours}:{self.minutes}:{self.seconds}"
                    data['result'] = 'appointment'

                elif data['act'] == 'note_time':
                    if self.hours != '00' and self.minutes != '00' and self.seconds != '00':
                        await message.answer(
                            f'Время для напоминания: {self.hours}:{self.minutes}:{self.seconds}',
                            reply_markup=self.inline_kb
                        )
                    await self.bot.send_message(message.chat.id, "Осталось оставить текст заметки:")
                    # async with self.state.proxy() as data:
                    app_day = data['date'].replace("/", "-")
                    data['date'] = f"{app_day} {self.hours}:{self.minutes}:{self.seconds}"
                    data['result'] = 'note_added'


def is_less_then_ten(hour, minute, second):
    """ Функция для более локаничного отображения времени """
    if hour < 10:
        hour = f"0{hour}"
    if minute < 10:
        minute = f"0{minute}"
    if second < 10:
        second = f"0{second}"
    return hour, minute, second
