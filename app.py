import datetime
import os
import random
import re

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QCalendarWidget, QLabel

import sys

from clients_db import WorkWithClientDB


class AppWindow(QMainWindow):

    def __init__(self):
        super(QMainWindow, self).__init__()

        # Положение заголовков и надписей добавления клиентов по вертикали
        add_client = 285
        hor_size = 590
        ver_size = 220
        self.horiz_move = 30
        self.index = 0
        self.is_digit_value = re.compile(r'\D+')

        # Вывод информации, либо о записанных клиентах, либо статистики
        self.info = QLabel(self)
        self.info.move(85, 250)
        self.info.setFont(QtGui.QFont("Times", 10, QtGui.QFont.Bold))

        # Заголовок окна
        self.setWindowTitle("LyubovNails")
        self.setGeometry(300, 250, 1200, 530)

        self.error_message = QLabel(self)
        self.error_message.setStyleSheet('color:red')
        self.error_message.move(500, 260)
        self.error_message.setFont(QtGui.QFont("Times", 10))

        self.is_right_phone_number = re.compile(r'^\+?[78][-\(]?\d{3}\)?-?\d{3}-?\d{2}-?\d{2}$')

        # вызов функции работы календаря (сразу отображает дату и данные)
        self.initUI()

        # Окошко подтверждения выхода
        btn = QtWidgets.QPushButton()
        btn.setToolTip("Close Application")
        btn.clicked.connect(self.closeEvent)

        # Основной заголовок в окне
        self.main_text = QtWidgets.QLabel(self)
        self.main_text.setText("Приложение для взаимодействия с базой данных клиентов")
        self.main_text.move(450, 10)
        self.main_text.adjustSize()

        # Заголовок добавления клиента
        self.header_text_appoint = QtWidgets.QLabel(self)
        self.header_text_appoint.setText("Действия с клиентом")
        self.header_text_appoint.move(540, 60)
        self.header_text_appoint.adjustSize()

        # Кнопка получения статистики
        self.stat_btn = QtWidgets.QPushButton(self)
        self.stat_btn.move(20, 20)
        self.stat_btn.setText("Статистика")
        self.stat_btn.setFixedSize(80, 30)
        self.stat_btn.clicked.connect(self.get_stat)

        # Надпись список клиентов
        self.clients_list_txt = QtWidgets.QLabel(self)
        self.clients_list_txt.setText("Список клиентов:")
        self.clients_list_txt.move(50, 100)
        self.clients_list_txt.adjustSize()

        # Выпадающий список клиентов
        self.clients_list = QtWidgets.QComboBox(self)
        self.renew_clients_list()
        self.clients_list.move(155, 95)
        self.clients_list.setFixedSize(600, 27)
        self.clients_list.activated[int].connect(self.on_activated_text)

        # Кнопка удаления клиента
        self.btn_del_cl = QtWidgets.QPushButton(self)
        self.btn_del_cl.move(415 + self.horiz_move, 140)
        self.btn_del_cl.setText("Удалить")
        self.btn_del_cl.setFixedSize(100, 30)
        self.btn_del_cl.clicked.connect(self.client_deleting)

        # Кнопка перезагрузки приложения
        self.btn_add_tel = QtWidgets.QPushButton(self)
        self.btn_add_tel.move(155 + self.horiz_move, 140)
        self.btn_add_tel.setText("Перезагрузка")
        self.btn_add_tel.setFixedSize(130, 30)
        self.btn_add_tel.clicked.connect(self.restart_app)

        # Кнопки изменения данных клиента
        self.btn_add_tel = QtWidgets.QPushButton(self)
        self.btn_add_tel.move(285 + self.horiz_move, 140)
        self.btn_add_tel.setText("Изменить данные")
        self.btn_add_tel.setFixedSize(130, 30)
        self.btn_add_tel.clicked.connect(self.change_info_window)

        self.btn_chng_name = QtWidgets.QPushButton(self)
        self.btn_chng_name.move(247 + self.horiz_move, 180)
        self.btn_chng_name.setEnabled(False)
        self.btn_chng_name.setText("Имя")
        self.btn_chng_name.setFixedSize(100, 30)

        # self.btn_chng_phone = QtWidgets.QPushButton(self)
        # self.btn_chng_phone.move(300 + self.horiz_move, 180)
        # self.btn_chng_phone.setEnabled(False)
        # self.btn_chng_phone.setText("Телефон")
        # self.btn_chng_phone.setFixedSize(100, 30)

        self.btn_chng_comment = QtWidgets.QPushButton(self)
        self.btn_chng_comment.move(352 + self.horiz_move, 180)
        self.btn_chng_comment.setEnabled(False)
        self.btn_chng_comment.setText("Комментарий")
        self.btn_chng_comment.setFixedSize(100, 30)

        # Кнопка записи клиента
        self.btn_app_cl = QtWidgets.QPushButton(self)
        self.btn_app_cl.move(55 + self.horiz_move, 140)
        self.btn_app_cl.setText("Записать")
        self.btn_app_cl.setFixedSize(100, 30)
        self.btn_app_cl.clicked.connect(self.appointment_info_window)

        # Заголовок указания времени
        self.time_txt = QLabel(self)
        self.time_txt.setText("Время")
        self.time_txt.move(385 + hor_size, 22 + ver_size)

        # Поле ввода комментария к записи клиента
        self.app_comment = QtWidgets.QTextEdit(self)
        self.app_comment.setPlaceholderText("Комментарий")
        self.app_comment.move(320 + hor_size, 90 + ver_size)
        self.app_comment.setFixedSize(160, 22)

        # Поле ввода часа записи
        self.hours_enter = QtWidgets.QLineEdit(self)
        self.hours_enter.setPlaceholderText("Ч")
        self.hours_enter.setMaxLength(2)
        self.hours_enter.move(375 + hor_size, 50 + ver_size)
        self.hours_enter.setFixedSize(22, 22)

        # Поле ввода минут записи
        self.min_enter = QtWidgets.QLineEdit(self)
        self.min_enter.setPlaceholderText("М")
        self.min_enter.setMaxLength(2)
        self.min_enter.move(405 + hor_size, 50 + ver_size)
        self.min_enter.setFixedSize(22, 22)

        # Двоеточие
        self.double_dots = QLabel(self)
        self.double_dots.setText(":")
        self.double_dots.move(399 + hor_size, 53 + ver_size)
        self.double_dots.adjustSize()

        # Кнопка отмены записи клиента
        self.btn_cancel_app = QtWidgets.QPushButton(self)
        self.btn_cancel_app.move(515 + self.horiz_move, 140)
        self.btn_cancel_app.setText("Отменить запись")
        self.btn_cancel_app.setFixedSize(130, 30)
        self.btn_cancel_app.clicked.connect(self.cancel_appointment)

        # Кнопка внесения суммы оплаты от клиента
        self.add_sum = QtWidgets.QPushButton(self)
        self.add_sum.move(645 + self.horiz_move, 140)
        self.add_sum.setText("Внести сумму")
        self.add_sum.setFixedSize(110, 30)
        self.add_sum.clicked.connect(self.add_payment)

        # Надпись ввода суммы
        self.payment_text = QtWidgets.QLabel(self)
        self.payment_text.move(560 + self.horiz_move, 185)

        # Окно ввода суммы
        self.payment_add_field = QtWidgets.QLineEdit(self)
        self.payment_add_field.move(650 + self.horiz_move, 180)
        self.payment_add_field.setEnabled(False)
        self.payment_add_field.setPlaceholderText("Сумма")
        self.payment_add_field.setFixedSize(100, 25)

        # Кнопка подтверждения добавления суммы
        self.btn_approve_payment = QtWidgets.QPushButton(self)
        self.btn_approve_payment.move(649 + self.horiz_move, 215)
        self.btn_approve_payment.setEnabled(False)
        self.btn_approve_payment.setText("Добавить")
        self.btn_approve_payment.setFixedSize(101, 30)
        self.btn_approve_payment.clicked.connect(self.approve_payment)

        # Заголовок добавления клиента
        self.header_text = QtWidgets.QLabel(self)
        self.header_text.setText("Добавление клиента")
        self.header_text.move(550, 90 + add_client)
        self.header_text.adjustSize()

        # Надпись ввода имени
        self.new_client = QtWidgets.QLabel(self)
        self.new_client.setText("Введите имя:")
        self.new_client.move(350, 127 + add_client)
        self.new_client.adjustSize()

        # Окно ввода имени
        self.name_add_field = QtWidgets.QLineEdit(self)
        self.name_add_field.setPlaceholderText("Имя")
        self.name_add_field.move(420, 123 + add_client)
        self.name_add_field.setFixedSize(160, 25)

        # # Надпись ввода телефона
        # self.new_phone = QtWidgets.QLabel(self)
        # self.new_phone.setText("Введите телефон:")
        # self.new_phone.move(354, 127 + add_client)
        # self.new_phone.adjustSize()
        #
        # # Окно ввода телефона
        # self.phone_add_field = QtWidgets.QLineEdit(self)
        # self.phone_add_field.setPlaceholderText("Телефон")
        # self.phone_add_field.move(465, 123 + add_client)
        # self.phone_add_field.setFixedSize(165, 25)

        # Надпись ввода комментария
        self.new_comment = QtWidgets.QLabel(self)
        self.new_comment.setText("Введите комментарий:")
        self.new_comment.move(645, 127 + add_client)
        self.new_comment.adjustSize()

        # Окно ввода комментария
        self.comment_add_field = QtWidgets.QLineEdit(self)
        self.comment_add_field.setPlaceholderText("Комментарий")
        self.comment_add_field.move(763, 123 + add_client)
        self.comment_add_field.setFixedSize(170, 25)

        # Кнопка добавления нового клиента
        self.btn_add_cl = QtWidgets.QPushButton(self)
        self.btn_add_cl.move(1030, 120 + add_client)
        self.btn_add_cl.setText("Добавить")
        self.btn_add_cl.setFixedSize(100, 30)
        self.btn_add_cl.clicked.connect(self.client_adding)

    # Функция работы с календарём
    def initUI(self):
        cal = QCalendarWidget(self)
        cal.setGridVisible(True)
        cal.move(830, 20)
        cal.clicked[QDate].connect(self.showDate)
        cal.adjustSize()

        self.lbl = QLabel(self)
        date = cal.selectedDate()
        self.lbl.setText(date.toString())
        self.date_formatting(date)
        self.lbl.move(955, 210)

    def showDate(self, date):
        self.date_formatting(date)

        self.app_list = []
        for appoint in self.date_info:
            self.app_date, comment, client, amount = appoint
            app_time = self.app_date.split(" ")[1]
            if comment is None and amount is None:
                string = f"{app_time} {client}"
            elif amount is None:
                string = f"{app_time} {client} {comment}"
            elif comment is None:
                string = f"{app_time} {client} {amount}р"
            else:
                string = f"{app_time} {client} {comment} {amount}р."
            self.app_list.append(string)
        if len(self.app_list) != 0:
            self.error_message.clear()
            self.info.clear()
            if datetime.datetime.strptime(self.app_date, "%d-%m-%Y %H:%M:%S") > datetime.datetime.now():
                string = "На этот день записаны:\n\n"
            else:
                string = "В этот день были записаны:\n\n"
            result = "\n\n".join(self.app_list)
            self.info.setText(string + result)
            self.info.adjustSize()
        else:
            self.info.clear()
            self.error_message.clear()
            self.error_message.setText("На данное число записей не было!")
            self.error_message.adjustSize()

    def date_formatting(self, date):

        month_dict = {"янв": "Jan",
                      "фев": "Feb",
                      "мар": "Mar",
                      "апр": "Apr",
                      "май": "May",
                      "июн": "Jun",
                      "июл": "Jul",
                      "авг": "Aug",
                      "сен": "Sep",
                      "окт": "Oct",
                      "ноя": "Nov",
                      "дек": "Dec"}

        self.lbl.setText(date.toString())

        date_raw = self.lbl.text()
        date_without_dayname = "/".join(date_raw.split(" ")[1:])

        for month in month_dict.keys():
            if month in date_without_dayname:
                unformatted_date = date_without_dayname.replace(month, month_dict[month])
                break

        self.date = str(datetime.datetime.strftime(datetime.datetime.strptime(f"{unformatted_date}", "%b/%d/%Y"),
                                                   "%d-%m-%Y"))
        self.date_info = WorkWithClientDB.show_appointment_info_by_date(f"{self.date}%")

    # Функция добавления клиента
    def client_adding(self):
        self.info.clear()
        self.switching_off_payment_btns()
        self.switching_off_chng_btns()
        # phone = self.phone_add_field.text()
        name = self.name_add_field.text()
        comment = self.comment_add_field.text()
        # if self.is_right_phone_number.match(phone):
        WorkWithClientDB.client_create(name, comment)
        self.name_add_field.clear()
        # self.phone_add_field.clear()
        self.comment_add_field.clear()
        self.renew_clients_list()
        # else:
        #     self.error_message.clear()
        #     self.error_message.setText("Введите правильно номер телефона!")
        #     self.error_message.adjustSize()

    # Функция удаления клиента
    def client_deleting(self):
        self.info.clear()
        self.switching_off_payment_btns()
        self.switching_off_chng_btns()
        self.client_del_window = ClientDeleting(self.index)
        self.client_del_window.show()

    # Функция определения выбора в выпадающем списке клиентов
    @QtCore.pyqtSlot(int)
    def on_activated_text(self):
        self.info.clear()
        self.switching_off_chng_btns()
        self.index = self.clients_list.currentIndex()
        self.get_ID(self.index)

    def get_ID(self, index):
        ID = re.findall(r'(\d+)', str(self.ids[index]))
        return ID[0]

    # Обновление выпадающего списка клиентов
    def renew_clients_list(self):
        self.clients_list.clear()
        clients_list = WorkWithClientDB.show_clients_list()
        if clients_list is None:
            self.error_message.clear()
            self.error_message.setText("Произошла ошибка при загрузке списка клиентов!\n\nБаза данных пуста, "
                                       "либо возникла ошибка при запросе к БД")
            self.error_message.adjustSize()
            self.result = []
        else:
            self.ids = []
            self.result = []
            for info in clients_list:
                cl_id, name, comment = info
                string = f"{name}    {comment}"
                self.result.append(string)
                self.ids.append(cl_id)
        self.clients_list.addItems(self.result)

    # Вызов окна с выбором данных о клиенте для обновления
    def change_info_window(self):
        self.info.clear()
        self.btn_chng_name.setEnabled(True)
        self.btn_chng_name.clicked.connect(self.client_name_changing)

        # self.btn_chng_phone.setEnabled(True)
        # self.btn_chng_phone.clicked.connect(self.client_phone_changing)

        self.btn_chng_comment.setEnabled(True)
        self.btn_chng_comment.clicked.connect(self.client_comment_changing)

    # Вызов окна подтверждения записи клиента и валидации введённой даты и времени
    def appointment_info_window(self):
        date_lst = []
        self.info.clear()
        self.switching_off_payment_btns()
        self.switching_off_chng_btns()
        result = WorkWithClientDB.show_appointment_info_by_cl_id(int(self.get_ID(self.index)))
        if len(result) != 0:
            for info in result:
                _, app_date, _, _, _ = info
                date_lst.append(datetime.datetime.strptime(f"{app_date}", "%d-%m-%Y %H:%M:%S"))
            app_date = max(date_lst)
        if len(result) == 0 or app_date < datetime.datetime.now():
            hours = self.hours_enter.text()
            minutes = self.min_enter.text()

            if hours == "":
                hours = "00"
            if minutes == "":
                minutes = "00"

            if self.is_digit_value.match(hours) or int(hours) > 23 or int(hours) < 0 or len(hours) > 2:
                self.error_message.clear()
                self.hours_enter.clear()
                self.error_message.setText("Введите правильно час приёма!")
                self.error_message.adjustSize()
            elif self.is_digit_value.match(minutes) or int(minutes) > 59 or int(minutes) < 0 or len(minutes) > 2:
                self.error_message.clear()
                self.min_enter.clear()
                self.error_message.setText("Введите правильно минуты приёма!")
                self.error_message.adjustSize()
            else:
                datetime_date = datetime.datetime.strptime(f"{self.date} {hours}:{minutes}", "%d-%m-%Y %H:%M")

                if datetime_date < datetime.datetime.now():
                    self.error_message.clear()
                    self.error_message.setText("Выберите верную дату!")
                    self.error_message.adjustSize()
                else:
                    date = datetime.datetime.strftime(datetime_date, "%d-%m-%Y %H:%M:%S")
                    cl_id = int(AppWindow().get_ID(self.index))
                    appmnt_description = self.app_comment.toPlainText()
                    WorkWithClientDB.make_appointment(cl_id, date, appmnt_description)
                    self.approve = ApproveAppoint(cl_id, date)
                    self.approve.show()
        elif app_date > datetime.datetime.now():
            date, time = app_date.strftime("%d-%m-%Y %H:%M:%S").split(" ")
            self.error_message.clear()
            self.error_message.setText(f"Клиент уже записан на {date} в {time}!")
            self.error_message.adjustSize()

    # Функция перезагрузки приложения
    def restart_app(self):
        self.restart()
        self.close()

    # Функция вызова окна отмены записи
    def cancel_appointment(self):
        self.switching_off_payment_btns()
        self.switching_off_chng_btns()
        info = WorkWithClientDB.show_appointment_info_by_cl_id(int(self.get_ID(self.index)))
        if len(info) != 0:
            self.cncl_appntmnt_window = CancelAppointment(self.index, info)
            self.cncl_appntmnt_window.show()
        else:
            self.error_message.clear()
            self.error_message.setText("Данный клиент ещё не записан!")
            self.error_message.adjustSize()

    # Перезагрузка главного окна
    @staticmethod
    def restart():
        QtCore.QCoreApplication.quit()
        QtCore.QProcess.startDetached(sys.executable, sys.argv)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Выход",
            "Вы действительно хотите выйти?",
            QMessageBox.Close | QMessageBox.Cancel)

        if reply == QMessageBox.Close:
            event.accept()
        else:
            event.ignore()

    def client_name_changing(self):
        self.ch_name = ChangeClientNameWindow(self.index)
        self.ch_name.show()
        self.switching_off_chng_btns()

    # def client_phone_changing(self):
    #     self.ch_phone = ChangeClientPhoneWindow(self.index)
    #     self.ch_phone.show()
    #     self.switching_off_chng_btns()

    def client_comment_changing(self):
        self.ch_comment = ChangeClientCommentWindow(self.index)
        self.ch_comment.show()
        self.switching_off_chng_btns()

    def client_sum_changing(self, name, pay_sum, cl_id, app_date):
        self.ch_sum = ChangeClientSumWindow(self.index, name, pay_sum, cl_id, app_date)
        self.ch_sum.show()
        self.switching_off_chng_btns()

    def switching_off_chng_btns(self):
        self.btn_chng_name.setEnabled(False)
        # self.btn_chng_phone.setEnabled(False)
        self.btn_chng_comment.setEnabled(False)

    # Функция добавления оплаты
    def add_payment(self):
        self.switching_off_chng_btns()
        if len(self.date_info) == 0:
            self.error_message.clear()
            self.error_message.setText("На данное число записей не было!")
            self.error_message.adjustSize()
        elif datetime.datetime.strptime(f"{self.app_date}", "%d-%m-%Y %H:%M:%S") >= datetime.datetime.now():
            self.error_message.clear()
            self.error_message.setText("Выберите прошедшую дату или сегодня,\n\tно уже прошедшее время!")
            self.error_message.adjustSize()
        else:
            self.error_message.clear()
            self.error_message.setText("Не забудьте выбрать клиента из списка!")
            self.error_message.adjustSize()

            self.payment_text.setText("Введите сумму:")
            self.payment_text.adjustSize()
            self.payment_add_field.setEnabled(True)
            self.btn_approve_payment.setEnabled(True)

    # Функция потверждения оплаты
    def approve_payment(self):
        pay_sum = self.payment_add_field.text()
        if pay_sum == "":
            self.error_message.clear()
            self.error_message.setText("Не введена сумма оплаты!")
            self.error_message.adjustSize()
        elif self.is_digit_value.match(pay_sum):
            self.error_message.clear()
            self.error_message.setText("Введено не число!")
            self.error_message.adjustSize()
        else:
            self.error_message.clear()
            cl_id = self.get_ID(self.index)
            cl_name = WorkWithClientDB.show_client_info(cl_id)[1]
            cl_app_info = WorkWithClientDB.show_appointment_info_by_cl_id(int(cl_id))
            if len(self.date_info) == 0:
                self.error_message.clear()
                self.error_message.setText("На данное число записей нет!")
                self.error_message.adjustSize()
            elif len(cl_app_info) == 0:
                self.error_message.clear()
                self.error_message.setText(" " * 8 +
                                           "Вы неверно выбрали клиента!\n\nТакого клиента в этот день не "
                                           "записано!")
                self.error_message.adjustSize()
            else:
                chck_date = datetime.datetime.strptime(f"{self.app_date}", "%d-%m-%Y %H:%M:%S")
                for info in cl_app_info:
                    name, app_date, description, price = info
                    date = datetime.datetime.strptime(f"{app_date}", "%d-%m-%Y %H:%M:%S")
                    if date < datetime.datetime.now() and date == chck_date:
                        amount = price
                        if amount is None:
                            WorkWithClientDB.add_profit(int(pay_sum), cl_id, app_date)

                            self.switching_off_payment_btns()
                            self.error_message.clear()

                            self.approve_pay_window = ApprovePaymentAdding(cl_name, app_date, pay_sum)
                            self.approve_pay_window.show()
                            self.payment_add_field.clear()

                        else:
                            self.client_sum_changing(cl_name, pay_sum, cl_id, app_date)
                        break
                    else:
                        self.error_message.clear()
                        self.error_message.setText("Выбранная дата не совпала с датами\nзаписи для выбранного клиента")
                        self.error_message.adjustSize()

    # Функция отключения кнопок
    def switching_off_payment_btns(self):
        self.btn_approve_payment.setEnabled(False)
        self.payment_add_field.setEnabled(False)

    # Функция получения статистики
    def get_stat(self):
        self.switching_off_payment_btns()
        self.switching_off_chng_btns()
        self.info.clear()
        self.error_message.clear()

        string = WorkWithClientDB.get_statistics()

        self.info.setText(string)
        self.info.adjustSize()


class ChangeClientNameWindow(QtWidgets.QDialog):

    def __init__(self, index):
        super(ChangeClientNameWindow, self).__init__()

        self.index = index
        self.main = AppWindow()

        self.setWindowTitle("Изменение имени клиента")
        self.setGeometry(600, 500, 350, 170)

        self.name_ch_field = QtWidgets.QLineEdit(self)
        self.name_ch_field.setPlaceholderText("Введите новое имя")
        self.name_ch_field.move(75, 40)
        self.name_ch_field.setFixedSize(200, 25)

        self.btn_aprv_name = QtWidgets.QPushButton(self)
        self.btn_aprv_name.move(125, 90)
        self.btn_aprv_name.setText("Подтвердить")
        self.btn_aprv_name.setFixedSize(100, 30)
        self.btn_aprv_name.clicked.connect(self.approving)

    def approving(self):
        name = self.name_ch_field.text()
        field = "name"
        cl_id = int(AppWindow().get_ID(self.index))
        WorkWithClientDB.change_client_info(field, name, cl_id)
        self.close()
        self.main.restart()


# class ChangeClientPhoneWindow(QtWidgets.QDialog):
#
#     def __init__(self, index):
#         super(ChangeClientPhoneWindow, self).__init__()
#
#         self.index = index
#         self.main = AppWindow()
#
#         self.setWindowTitle("Изменение телефона клиента")
#         self.setGeometry(600, 500, 350, 170)
#
#         self.error_t = QLabel(self)
#         self.error_t.move(82, 73)
#
#         self.phone_ch_field = QtWidgets.QLineEdit(self)
#         self.phone_ch_field.setPlaceholderText("Введите новый телефон")
#         self.phone_ch_field.move(95, 40)
#         self.phone_ch_field.setFixedSize(165, 25)
#
#         self.btn_aprv_phone = QtWidgets.QPushButton(self)
#         self.btn_aprv_phone.move(125, 100)
#         self.btn_aprv_phone.setText("Подтвердить")
#         self.btn_aprv_phone.setFixedSize(100, 30)
#         self.btn_aprv_phone.clicked.connect(self.approving)
#
#     def approving(self):
#         phone = self.phone_ch_field.text()
#         main = AppWindow()
#         if main.is_right_phone_number.match(phone):
#             field = "phone"
#             cl_id = int(AppWindow().get_ID(self.index))
#             WorkWithClientDB.change_client_info(field, phone, cl_id)
#             self.close()
#             self.main.restart()
#         else:
#             self.error_t.setText("Введите номер телефона правильно!")
#             self.error_t.adjustSize()


class ChangeClientCommentWindow(QtWidgets.QDialog):

    def __init__(self, index):
        super(ChangeClientCommentWindow, self).__init__()

        self.index = index
        self.main = AppWindow()

        self.setWindowTitle("Изменение комментария о клиенте")
        self.setGeometry(600, 500, 350, 170)

        self.comment_ch_field = QtWidgets.QLineEdit(self)
        self.comment_ch_field.setPlaceholderText("Введите новый комментарий")
        self.comment_ch_field.move(88, 40)
        self.comment_ch_field.setFixedSize(170, 25)

        self.btn_aprv_comment = QtWidgets.QPushButton(self)
        self.btn_aprv_comment.move(125, 90)
        self.btn_aprv_comment.setText("Подтвердить")
        self.btn_aprv_comment.setFixedSize(100, 30)
        self.btn_aprv_comment.clicked.connect(self.approving)

    def approving(self):
        comment = self.comment_ch_field.text()
        field = "description"
        cl_id = int(AppWindow().get_ID(self.index))
        WorkWithClientDB.change_client_info(field, comment, cl_id)
        self.close()
        self.main.restart()


class ChangeClientSumWindow(QtWidgets.QDialog):

    def __init__(self, index, name, pay_sum, cl_id, app_date):
        super(ChangeClientSumWindow, self).__init__()

        self.index = index
        self.name = name
        self.pay_sum = pay_sum
        self.cl_id = cl_id
        self.app_date = app_date
        self.main = AppWindow()

        self.error_sum = QLabel(self)
        self.error_sum.setStyleSheet('color:red')
        self.error_sum.move(50, 50)
        self.error_sum.setFont(QtGui.QFont("Times", 10))

        self.setWindowTitle("Изменение суммы оплаты клиента")
        self.setGeometry(600, 500, 350, 170)

        self.error_message = QLabel(self)
        self.error_message.move(15, 2)
        self.error_message.setText("На данную дату и данного клиента уже внесена информация\n\t\t\tоб "
                                   "оплате")
        self.error_message.adjustSize()

        self.sum_ch_field = QtWidgets.QLineEdit(self)
        self.sum_ch_field.setPlaceholderText("Введите новое значение суммы")
        self.sum_ch_field.move(88, 40)
        self.sum_ch_field.setFixedSize(170, 25)

        self.btn_aprv_sum = QtWidgets.QPushButton(self)
        self.btn_aprv_sum.move(68, 90)
        self.btn_aprv_sum.setText("Подтвердить")
        self.btn_aprv_sum.setFixedSize(100, 30)
        self.btn_aprv_sum.clicked.connect(self.approving)

        self.btn_cancel_sum = QtWidgets.QPushButton(self)
        self.btn_cancel_sum.move(170, 90)
        self.btn_cancel_sum.setText("Отмена")
        self.btn_cancel_sum.setFixedSize(105, 30)
        self.btn_cancel_sum.clicked.connect(self.btnClosed)

    def approving(self):
        WorkWithClientDB.add_profit(int(self.pay_sum), self.cl_id, self.app_date)
        self.approve_pay_window = ApprovePaymentAdding(self.name, self.app_date, self.pay_sum)
        self.approve_pay_window.show()
        self.close()

    def btnClosed(self):
        self.close()


class ApproveAppoint(QtWidgets.QDialog):
    def __init__(self, cl_id, date):
        super(ApproveAppoint, self).__init__()

        self.result = QtWidgets.QLabel(self)
        info = WorkWithClientDB.show_client_info(int(cl_id))
        _, name, comment = info
        string = f"Вы записали {name} на {date}; {comment}"
        self.result.setText(string)
        self.result.setAlignment(Qt.AlignHCenter)
        self.result.adjustSize()

        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setObjectName("pushButton")

        self.pushButton.setFixedSize(100, 30)
        self.pushButton.clicked.connect(self.btnClosed)

        self.setWindowTitle("Подтверждение")
        self.setGeometry(500, 500, 480, 120)
        self.pushButton.setText("ok")

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.result)
        self.verticalLayout.addWidget(self.pushButton, alignment=QtCore.Qt.AlignHCenter)

    def btnClosed(self):
        main = AppWindow()
        main.app_comment.clear()
        main.hours_enter.clear()
        main.min_enter.clear()
        self.close()


class CancelAppointment(QtWidgets.QDialog):
    def __init__(self, index, info):
        super(CancelAppointment, self).__init__()
        self.index = index
        self.cl_id = int(AppWindow().get_ID(self.index))

        self.result = QtWidgets.QLabel(self)
        date_lst = []
        if len(info) >= 1:
            for i in info:
                name, app_date, _, _ = i
                date_lst.append(datetime.datetime.strptime(f"{app_date}", "%d-%m-%Y %H:%M:%S"))
            app_date = max(date_lst)
            string = f"\n\n{name.capitalize()} записан на {app_date}\n\n\nВы действительно хотите отменить запись?"
        else:
            name, app_date, _, _ = info
            string = f"\n\n{name.capitalize()} записан на {app_date}\n\n\nВы действительно хотите отменить запись?"

        self.result.setText(string)
        self.result.setAlignment(Qt.AlignHCenter)
        self.result.adjustSize()

        self.setWindowTitle("Отмена записи")
        self.setGeometry(500, 500, 350, 200)

        self.pushButtonYes = QtWidgets.QPushButton(self)
        self.pushButtonYes.setText("Да")
        self.pushButtonYes.setFixedSize(100, 30)
        self.pushButtonYes.move(70, 135)
        self.pushButtonYes.clicked.connect(self.cancel_appointment)

        self.pushButtonNo = QtWidgets.QPushButton(self)
        self.pushButtonNo.setText("Нет")
        self.pushButtonNo.setFixedSize(100, 30)
        self.pushButtonNo.move(180, 135)
        self.pushButtonNo.clicked.connect(self.btnClosed)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.result)

    def btnClosed(self):
        self.close()

    def cancel_appointment(self):
        WorkWithClientDB.cancel_appointment(self.cl_id)
        self.close()


class ClientDeleting(QtWidgets.QDialog):
    def __init__(self, index):
        super(ClientDeleting, self).__init__()

        self.index = index
        self.main = AppWindow()

        self.cl_id = int(self.main.get_ID(self.index))
        self.main = AppWindow()

        self.result = QtWidgets.QLabel(self)

        result = WorkWithClientDB.show_client_info(self.cl_id)
        _, name, _ = result
        string = f'\n\nВы действительно хотите удалить "{name.capitalize()}"?'

        self.result.setText(string)
        self.result.setAlignment(Qt.AlignHCenter)
        self.result.adjustSize()

        self.setWindowTitle("Удаление клиента")
        self.setGeometry(500, 500, 300, 150)

        self.pushButtonYes = QtWidgets.QPushButton(self)
        self.pushButtonYes.setText("Да")
        self.pushButtonYes.setFixedSize(100, 30)
        self.pushButtonYes.move(45, 90)
        self.pushButtonYes.clicked.connect(self.del_cl_approve)

        self.pushButtonNo = QtWidgets.QPushButton(self)
        self.pushButtonNo.setText("Нет")
        self.pushButtonNo.setFixedSize(100, 30)
        self.pushButtonNo.move(155, 90)
        self.pushButtonNo.clicked.connect(self.btnClosed)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.result)

    def del_cl_approve(self):
        WorkWithClientDB.del_client(self.main.get_ID(self.index))
        self.close()
        self.main.restart()

    def btnClosed(self):
        self.close()


class ApprovePaymentAdding(QtWidgets.QDialog):
    def __init__(self, cl_name, str_app_date, pay_sum):
        super(ApprovePaymentAdding, self).__init__()

        self.name = cl_name.capitalize()
        self.result = QtWidgets.QLabel(self)
        self.main = AppWindow()

        app_date = str_app_date.split(" ")[0]

        string = f"Вы внесли сумму оплаты для {cl_name}\n\n\tза {app_date} в размере {pay_sum} рублей"

        self.result.setText(string)
        self.result.setAlignment(Qt.AlignCenter)
        self.result.adjustSize()

        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setObjectName("pushButton")

        self.pushButton.setFixedSize(100, 30)
        self.pushButton.clicked.connect(self.btnClosed)

        self.setWindowTitle("Подтверждение")
        self.setGeometry(500, 500, 300, 130)
        self.pushButton.setText("ok")

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.result)
        self.verticalLayout.addWidget(self.pushButton, alignment=QtCore.Qt.AlignHCenter)

    def btnClosed(self):
        self.main.switching_off_payment_btns()
        self.main.switching_off_chng_btns()
        self.close()


def application():
    app = QApplication(sys.argv)
    window = AppWindow()
    window.setObjectName("MainWindow")
    file_list = []
    for file in os.listdir():
        if file.endswith(".jpg"):
            file_list.append(file)
    rnd_file = random.choice(file_list)
    window.setStyleSheet("#MainWindow{border-image:url" + f"({rnd_file})" + "}")
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap("icon.png"),
                   QtGui.QIcon.Selected, QtGui.QIcon.On)
    window.setWindowIcon(icon)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    application()
