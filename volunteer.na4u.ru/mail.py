import smtplib as smtp
import sqlite3

#Библиотека для работы с кириллицей
from email.mime.text import MIMEText
from email.header    import Header
import json


def to_volunteer(destination, link, name):
    """to_volunteer(destination, link)"""
    # читаем файл конфиг, берем из него логин и пароль для smtp
    fp = open('conn.fig')
    s = fp.read()
    dic = json.loads(s)    
    login = dic.get('login')
    fp.close()

    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    text = cur.execute('SELECT theme, body FROM pages WHERE place = "to_volunteer"').fetchone()
    conn.close()

    msg = MIMEText(text[1].format(name=name, link=link), 'plain', 'utf-8')
    msg['Subject'] = Header(text[0], 'utf-8')
    msg['From'] = login
    msg['To'] = destination
    
    server = smtp.SMTP('localhost', 25)
    server.set_debuglevel(0)
    server.sendmail(login, destination, msg.as_string())
    server.quit()


def send_passw(destination: 'dest_adr', log: 'login', pwd: 'password', name) -> None:
    # читаем файл конфиг, берем из него логин и пароль для smtp
    fp = open('conn.fig')
    s = fp.read()
    dic = json.loads(s)    
    login = dic.get('login')
    fp.close()

    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    text = cur.execute('SELECT theme, body FROM pages WHERE place = "send_passw"').fetchone()
    conn.close()

    msg = MIMEText(text[1].format(name=name, log=log, pwd=pwd, link='https://volunteer.na4u.ru/login'))
    msg['Subject'] = Header(text[0], 'utf-8')
    msg['From'] = login
    msg['To'] = destination

    server = smtp.SMTP('localhost', 25)
    server.sendmail(login, destination, msg.as_string())
    server.quit


def send_recovery(destination: 'dest_adr', log: 'login', pwd: 'password') -> None:
    # читаем файл конфиг, берем из него логин и пароль для smtp
    fp = open('conn.fig')
    s = fp.read()
    dic = json.loads(s)    
    login = dic.get('login')
    fp.close()

    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    text = cur.execute('SELECT theme, body FROM pages WHERE place = "send_recovery"').fetchone()
    conn.close()

    msg = MIMEText(text[1].format(log=log, pwd=pwd))
    msg['Subject'] = Header(text[0], 'utf-8')
    msg['From'] = login
    msg['To'] = destination

    server = smtp.SMTP('localhost', 25)
#    server.ehlo()
#    if server.has_extn('STARTTLS'):
#        server.starttls()
#        server.ehlo()
#    server.login(login, password)
    server.sendmail(login, destination, msg.as_string())
    server.quit()


if __name__ == '__main__':
    to_volunteer('patro1@yandex.ru', 'Тест-сообщение о регистрации')
    send_passw('patro1@yandex.ru', 'Тест-сообщение с логином и паролем')
