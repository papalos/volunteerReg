import sqlite3
import smtplib as smtp
#Библиотека для работы с кириллицей
from email.mime.text import MIMEText
from email.header import Header
import json


def get_evt_reserve():
    """ Получаем количество максимально требуемых мест на событии """
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # 1) Получаем id событий из резерва
    # 2) Находим для них максимальное количество требуемых волонтеров
    cur.execute("SELECT id_evt, staff_max + classroom_max FROM event WHERE id_evt IN (SELECT DISTINCT id_evt FROM reserve)")
    _dict = {x[0]: x[1] for x in cur.fetchall()}
    conn.close()
    return _dict


def get_evt_freed(max_site_on_evt):
    """ 
    Сравниваем количество мест с количеством зарегистрированных 
    и возвращаем словарь событий, на которых появились свободные места с количеством недостающих мест
    """
    # Из переданного списка забираем id событий
    ls_evt = tuple([x for x in max_site_on_evt])+(-1,) # Чтобы кортеж не состоял из одного элемента

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # По списку событий ищем сколько на них зарегистрированно
    cur.execute("SELECT id_evt, COUNT(id_evt) FROM registration WHERE id_evt IN {} GROUP BY id_evt".format(ls_evt))
    reg_on_evt = cur.fetchall()
    conn.close()
    # Возвращаем словарь с событиями с количеством освободившихся мест при условии что места на них освободились
    return {x[0]:  max_site_on_evt[x[0]] - x[1] for x in reg_on_evt if x[1] < max_site_on_evt[x[0]]}


def send(destination, name_evt):
    # читаем файл конфиг, берем из него логин и пароль для smtp
    fp = open('conn.fig')
    s = fp.read()
    dic = json.loads(s)    
    login = dic.get('login')
    fp.close()

    # Создаем тело сообщения
    conn = sqlite3.connect("sql/volonteer.db")
    cursor = conn.cursor()
    # По списку событий ищем сколько на них зарегистрированно
    cursor.execute("SELECT theme, body FROM pages WHERE place = 'reserve_send'")
    text = cursor.fetchone()
    #print(text)
    conn.close()
    msg = MIMEText(text[1].format(event=name_evt), 'plain', 'utf-8')
    msg['Subject'] = Header(text[0], 'utf-8')
    msg['From'] = login
    msg['To'] = destination
    
    # Поключаемся к серверу и отправляем сообщение

    server = smtp.SMTP('localhost', 25)
    server.set_debuglevel(0)
    server.sendmail(login, destination, msg.as_string())
    server.quit()


def main():
    conn = sqlite3.connect("sql/volonteer.db")
    curI = conn.cursor()
    curII = conn.cursor()
    evt_reserve = get_evt_reserve()
    for event, sites in get_evt_freed(evt_reserve).items():
            # Получаем список id добавленных в резерв пользователей, места на которые освободились, не более количества освободившихся мест
            curI.execute("SELECT id_prsn, email FROM reserve WHERE id_evt == {} LIMIT {}".format(event, sites))
            # Получаем названия этих событий
            curII.execute("SELECT activity FROM event WHERE id_evt == {}".format(event))
            event_name = curII.fetchone()[0]
            curIII = conn.cursor()
            for i in curI.fetchall():
                # print(i, event)
                # Перебирая эти события, этих пользователей сообщаем им об осободившихся местах на событие в резерве
                send(i[1], event_name)
                # Удаляем запись с этим событием и пользователем из таблицы резерва
                curIII.execute('DELETE FROM reserve WHERE id_evt == (?) AND id_prsn == (?)', (event, i[0]))
            conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
