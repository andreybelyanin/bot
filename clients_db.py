from datetime import datetime
import sqlite3

conn = sqlite3.connect("clients.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()


class WorkWithClientDB:

    @staticmethod
    def show_clients_list():
        try:
            cursor.execute("""SELECT id, name, description FROM clients ORDER BY name;""")
            clients_list = cursor.fetchall()
            return clients_list
        except Exception as e:
            err_msg = f"Произошла ошибка в {datetime.now()} при формировании списка клиентов: {e}\n "
            WorkWithClientDB.writing_error_log(err_msg)

    @staticmethod
    def show_client_info(cl_id: int):
        try:
            cursor.execute("""SELECT id, name, description FROM clients WHERE id = ?""", (cl_id,))
            client_info = cursor.fetchone()
            return client_info
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о клиенте: {e}\n")

    @staticmethod
    def client_create(name: str, description: str):
        cursor.execute("SELECT max(id) FROM clients;")
        max_clients_id = cursor.fetchone()
        if max_clients_id[0] is None:
            cl_id = 1
        else:
            cl_id = max_clients_id[0] + 1
        cl_entity = (cl_id, name, description)
        try:
            cursor.execute("""INSERT or IGNORE INTO clients(id, name, description)
                                values(?, ?, ?)""", cl_entity)
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при добавлении клиента: {e}\n")

    @staticmethod
    def change_client_info(field: str, value: str, cl_id: int):
        try:
            cursor.execute(f"UPDATE clients SET {field} = ? WHERE id = ?", (value, cl_id))
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"изменении данных клиента: {e}\n")

    @staticmethod
    def make_appointment(cl_id: int, appmnt_date: str, appmnt_description: str):
        cursor.execute("SELECT max(id) FROM appointment")
        max_ap_id = cursor.fetchone()
        if not max_ap_id[0]:
            ap_id = 1
        else:
            ap_id = max_ap_id[0] + 1
        ap_entity = (ap_id, appmnt_date, appmnt_description, cl_id)
        try:
            cursor.execute(f"""INSERT or IGNORE INTO appointment (id, appointment_date, description, client_id)
                                values (?, ?, ?, ?)""", ap_entity)
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при записи клиента: {e}\n")

    @staticmethod
    def cancel_appointment(cl_id: int):
        try:
            cursor.execute(f"DELETE FROM appointment WHERE client_id = ?", (cl_id,))
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла в {datetime.now()} ошибка при удалении записи: {e}\n")

    @staticmethod
    def add_profit(profit: int, cl_id: int, app_date: str):
        try:
            cursor.execute(f"""UPDATE appointment SET price = ?
                           WHERE client_id = ? AND appointment_date = ?""", (profit, cl_id, app_date))
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"добавлении суммы оплаты: {e}\n")

    @staticmethod
    def show_appointment_info_by_date(date: str):
        try:
            cursor.execute("""SELECT ap.appointment_date, ap.description, cl.name, ap.price FROM appointment ap
            JOIN clients cl ON ap.client_id = cl.id WHERE ap.appointment_date LIKE ?""", (date,))
            clients_list = cursor.fetchall()
            return clients_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при получении информации о "
                                               f"записи по дате: {e}\n")

    @staticmethod
    def show_appointment_info_by_cl_id(cl_id: int):
        try:
            cursor.execute(f"""SELECT name, appointment_date, ap.description, price FROM appointment ap
                                JOIN clients cl ON ap.client_id = cl.id WHERE ap.client_id = ?""", (cl_id,))
            clients_list = cursor.fetchall()
            return clients_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о записи: {e}\n")

    @staticmethod
    def del_client(cl_id):
        result = []
        try:
            cursor.execute(f"""SELECT name FROM clients WHERE id = ?""", (cl_id,))
            clients_del_list = cursor.fetchall()
            for row in clients_del_list:
                result.append(row)
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} "
                                               f"при поиске данного клиента({cl_id}): {e}\n")
        try:
            cursor.execute("DELETE FROM clients WHERE id = ?", (cl_id,))
            conn.commit()
            return f"Удалён клиент: {result}"
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка при удалении данного клиента({cl_id}): {e}\n")

    @staticmethod
    def get_statistics():
        try:
            cursor.execute(f"""select client_id, price, appointment_date from appointment""")
            month_stat_list = cursor.fetchall()

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
            cursor.execute(f"""SELECT note FROM notes WHERE note_date LIKE ?""", (date_spl_time,))
            notes_list = cursor.fetchall()
            return notes_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о заметках: {e}\n")

    @staticmethod
    def get_note_now(date):
        try:
            cursor.execute(f"""SELECT note FROM notes WHERE substring(note_date, 1, 16) = ?""", (date,))
            note = cursor.fetchone()
            return note
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                               f"получении информации о заметке: {e}\n")

    @staticmethod
    def add_note(note_date: str, note: str):
        try:
            cursor.execute(f"""INSERT or IGNORE INTO notes (note_date, note)
                                values (?, ?)""", (note_date, note))
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при добавлении заметки: {e}\n")

    @staticmethod
    def del_note(note_date: str, note: str):
        date_spl_time = note_date.split(" ")[0]
        try:
            cursor.execute(f"""DELETE FROM notes WHERE substring(note_date, 1, 10) = ? AND note = ?""", (date_spl_time,
                                                                                                         note))
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при добавлении заметки: {e}\n")

    @staticmethod
    def get_notes_for_month(date_tuple):
        if isinstance(date_tuple, tuple):
            try:
                cursor.execute(f"""SELECT note FROM notes WHERE substring(note_date, 1, 10) IN {date_tuple}""")
                notes_list = cursor.fetchall()
                return notes_list
            except Exception as e:
                WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при "
                                                   f"получении информации о заметках на месяц: {e}\n")
        elif isinstance(date_tuple, str):
            try:
                cursor.execute(f"""SELECT note FROM notes WHERE substring(note_date, 1, 10) IN (?)""", (date_tuple,))
                notes_list = cursor.fetchall()
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
            cursor.execute(f"""DELETE FROM notes WHERE note_date IN {date_tuple}""")
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при чистке БД от старых заметок: {e}\n")

    @staticmethod
    def db_appointment_cleaner(date_tuple):
        try:
            cursor.execute(f"""DELETE FROM appointment WHERE SUBSTRING(appointment_date,1,10) IN {date_tuple}""")
            conn.commit()
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при чистке БД от старых записей: {e}\n")

    @staticmethod
    def check_appointment(date_tuple):
        try:
            cursor.execute(f"""SELECT appointment_date from appointment WHERE SUBSTRING(appointment_date,1,10) IN {date_tuple}""")
            notes_list = cursor.fetchall()
            return notes_list
        except Exception as e:
            WorkWithClientDB.writing_error_log(f"Произошла ошибка в {datetime.now()} при запросе к appointment: {e}\n")


def _init_db():
    """Инициализирует БД"""
    with open("create_db.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='clients'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()


if __name__ == "__main__":
    check_db_exists()
