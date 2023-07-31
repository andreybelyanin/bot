import time
from datetime import datetime
import sqlite3

from sqlalchemy import func, select, update, delete, and_

from DBmodel import Session, Clients, Appointment, Notes, GPIO

conn = sqlite3.connect("clients.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()
session = Session()


class WorkWithClientDB:

    @staticmethod
    def show_clients_list():
        try:
            query = select(Clients.id, Clients.name, Clients.description).order_by(Clients.name)
            clients_list = session.execute(query).all()
            return clients_list
        except Exception as e:
            err_msg = f"Произошла ошибка в {datetime.now()} при формировании списка клиентов: {e}\n "
            WorkWithClientDB.writing_error_log(err_msg)

    @staticmethod
    def show_client_info(cl_id: int):
        try:
            query = select(Clients.id, Clients.name, Clients.description).where(Clients.id == cl_id)
            client_info = session.execute(query).one()
            return client_info
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о клиенте: {e}\n")

    @staticmethod
    def client_create(name: str, description: str):
        query = select(func.max(Clients.id))
        max_clients_id = session.execute(query).scalar()
        if max_clients_id is None:
            cl_id = 1
        else:
            cl_id = max_clients_id + 1
        try:
            new_client = Clients(id=cl_id, name=name, description=description)
            session.add(new_client)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при добавлении клиента: {e}\n")

    @staticmethod
    def change_client_info(field: str, value: str, cl_id: int):
        query = None
        try:
            if field == 'name':
                query = update(Clients).where(Clients.id == cl_id).values(name=value)
            elif field == 'description':
                query = update(Clients).where(Clients.id == cl_id).values(description=value)
            session.execute(query)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"изменении данных клиента: {e}\n")

    @staticmethod
    def make_appointment(cl_id: int, appmnt_date: str, appmnt_description: str):
        query = select(func.max(Appointment.id))
        max_ap_id = session.execute(query).scalar()
        if not max_ap_id:
            ap_id = 1
        else:
            ap_id = max_ap_id + 1
        try:
            new_app = Appointment(id=ap_id, appointment_date=appmnt_date, description=appmnt_description,
                                  client_id=cl_id)
            session.add(new_app)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при записи клиента: {e}\n")

    @staticmethod
    def cancel_appointment(cl_id: int):
        try:
            query = delete(Appointment).where(Appointment.client_id == cl_id)
            session.execute(query)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла в {datetime.now()} ошибка при удалении записи: {e}\n")

    @staticmethod
    def add_profit(profit: int, cl_id: int, app_date: str):
        try:
            query = update(Appointment).values(price=profit).where(and_(Appointment.client_id == cl_id,
                                                                        Appointment.appointment_date == app_date))
            session.execute(query)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"добавлении суммы оплаты: {e}\n")

    @staticmethod
    def show_appointment_info_by_date(date: str):
        try:
            query = select(Appointment.appointment_date, Appointment.description, Clients.name, Appointment.price).join(
                Clients).where(Appointment.appointment_date.like(date))
            clients_list = session.execute(query).all()
            return clients_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при получении информации о "
                                               f"записи по дате: {e}\n")

    @staticmethod
    def show_appointment_info_by_cl_id(cl_id: int):
        try:
            query = select(Clients.name, Appointment.appointment_date, Appointment.description, Appointment.price).join(
                Clients).where(Appointment.client_id == cl_id)
            clients_list = session.execute(query).all()
            return clients_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о записи: {e}\n")

    @staticmethod
    def del_client(cl_id):
        result = []
        try:
            query = select(Clients.name).where(Clients.id == cl_id)
            clients_del_list = session.execute(query).all()
            for row in clients_del_list:
                result.append(row)
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} "
                                               f"при поиске данного клиента({cl_id}): {e}\n")
        try:
            query = delete(Clients).where(Clients.id == cl_id)
            session.execute(query)
            session.commit()
            return f"Удалён клиент: {result}"
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка при удалении данного клиента({cl_id}): {e}\n")

    @staticmethod
    def get_statistics():
        try:
            query = select(Appointment.client_id, Appointment.price, Appointment.appointment_date)
            month_stat_list = session.execute(query).all()

            start_date = datetime.now()
            start_year = datetime(year=start_date.year, month=1, day=1)
            start_month = datetime(year=start_date.year, month=start_date.month, day=1)
            year_stat = []
            month_stat = []
            for item in month_stat_list:
                cl_id, amount, app_date = item
                app_date = datetime.strptime(f"{app_date}", "%d-%m-%Y %H:%M:%S")
                if start_year < app_date < datetime.now():
                    year_stat.append(item)
                if start_month < app_date < datetime.now():
                    month_stat.append(item)

            month_client_count = len(month_stat)
            year_client_count = len(year_stat)

            month_amount = 0
            year_amount = 0
            for item in month_stat:
                if item[1] is not None:
                    month_amount += item[1]
            for item in year_stat:
                if item[1] is not None:
                    year_amount += item[1]

            string = f"Клиентов за месяц: {month_client_count}\nВыручка за месяц: {month_amount} рублей\n" \
                     f"Клиентов за год: {year_client_count}\nВыручка за год: {year_amount} рублей"
            return string
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при сборе статистики по оплате "
                                               f"за месяц: {e}\n")

    @staticmethod
    def get_notes(date):
        date_spl_time = date.split(" ")[0]
        try:
            query = select(Notes.note).where(Notes.note_date.like(date_spl_time))
            notes_list = session.execute(query).all()
            return notes_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о заметках: {e}\n")

    @staticmethod
    def get_note_now(date):
        try:
            query = select(Notes.note).where((func.substr(Notes.note_date, 1, 16)) == date)
            note = session.execute(query).one()
            return note
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о заметке: {e}\n")

    @staticmethod
    def add_note(note_date: str, note: str):
        try:
            new_note = Notes(note_date=note_date, note=note)
            session.add(new_note)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при добавлении заметки: {e}\n")

    @staticmethod
    def del_note(note_date: str, note: str):
        date_spl_time = note_date.split(" ")[0]
        try:
            query = delete(Notes).where(and_(func.substr(Notes.note_date, 1, 10) == date_spl_time, Notes.note == note))
            session.execute(query)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при добавлении заметки: {e}\n")

    @staticmethod
    def get_notes_for_month(date_tuple):
        if isinstance(date_tuple, tuple):
            try:
                query = select(Notes.note).where((func.substr(Notes.note_date, 1, 10)).in_(date_tuple))
                notes_list = session.execute(query).all()
                return notes_list
            except Exception as e:
                WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                                   f"получении информации о заметках на месяц: {e}\n")
        elif isinstance(date_tuple, str):
            try:
                query = select(Notes.note).where((func.substr(Notes.note_date, 1, 10) == date_tuple))
                notes_list = session.execute(query).all()
                return notes_list
            except Exception as e:
                WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                                   f"получении информации о заметках на месяц: {e}\n")

    @staticmethod
    def writing_error_log(text):
        with open("err_log.txt", "a", encoding="utf-8") as log:
            log.write(text)

    @staticmethod
    def db_cleaner(date_tuple):
        try:
            query = delete(Notes).where(Notes.note_date.in_(date_tuple))
            session.execute(query)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(
                f"Произошла ошибка в {datetime.now()} при чистке БД от старых заметок: {e}\n")

    @staticmethod
    def db_appointment_cleaner(date_tuple):
        try:
            query = delete(Appointment).where((func.substr(Appointment.appointment_date, 1, 10)).in_(date_tuple))
            session.execute(query)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(
                f"Произошла ошибка в {datetime.now()} при чистке БД от старых записей: {e}\n")

    @staticmethod
    def check_appointment(date_tuple):
        try:
            query = select(Appointment.appointment_date).where((func.substr(Appointment.appointment_date, 1, 10)).in_(
                date_tuple
            ))
            app_dt_list = session.execute(query).all()
            return app_dt_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при запросе к appointment: {e}\n")

    @staticmethod
    def gpio_controlling(comand_num: int):
        try:
            query = update(GPIO).values(comand=comand_num).where(GPIO.id == 1)
            session.execute(query)
            session.commit()
            if comand_num == 1:
                time.sleep(3)
            elif comand_num == 2:
                time.sleep(7)
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"запуске команды {comand_num} для работы с GPIO: {e}\n")

    @staticmethod
    def check_comand():
        try:
            query = select(GPIO.comand).where(GPIO.id == 1)
            comand = session.execute(query).scalar()
            return int(comand)
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"проверке номера команды: {e}\n")

    @staticmethod
    def check_status():
        try:
            query = select(GPIO.status).where(GPIO.id == 1)
            status = session.execute(query).scalar()
            if int(status) == 1:
                return 'Сервер включен'
            else:
                return 'Сервер выключен'
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"проверке статуса сервера: {e}\n")

    @staticmethod
    def update_server_status(stat_name: int):
        try:
            query = update(GPIO).values(status=stat_name).where(GPIO.id == 1)
            session.execute(query)
            session.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"смене статуса сервера: {e}\n")


# def _init_db():
#     """Инициализирует БД"""
#     with open("create_db.sql", "r") as f:
#         sql = f.read()
#     cursor.executescript(sql)
#     conn.commit()
#
#
# def check_db_exists():
#     """Проверяет, инициализирована ли БД, если нет — инициализирует"""
#     cursor.execute("SELECT name FROM sqlite_master "
#                    "WHERE type='table' AND name='clients'")
#     table_exists = cursor.fetchall()
#     if table_exists:
#         return
#     _init_db()


if __name__ == "__main__":
    # check_db_exists()
    print(WorkWithClientDB.check_appointment(('21-07-2023',)))
