from flask import Flask, render_template, request, redirect, url_for, session   # инструменты Flask
import sqlite3                                                                  # для работы с БД SQLite
from datetime import date, timedelta                                            # класс для работы с датой
import random                                                                   # для генерации случайных чисел
import mail                                                                     # отправка сообщения для подтверждения регистрации
import checker                                                                  # проверяет, что на сайте админ
from noneisnull import nulling                                                  # преобразует None к нулю
from admin.admin import panel                                                   # Подключение Блюпринта администратора
from user.user import cabin                                                     # Подключение Блюпринта волонтера

app = Flask(__name__)
# Время жизни сессии
app.permanent_session_lifetime = timedelta(hours=1)

# Ключ шифорования для работы с сессиями
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

app.register_blueprint(panel, url_prefix='/admin')
app.register_blueprint(cabin, url_prefix='/us')


# ---------------- начало скрипта ----------------- #

# I Главная страница
# Новости. Вход в личные кабинеты участников и админа. Переход к регистрации
@app.route('/')
def index():
    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM news ORDER BY date DESC LIMIT 10')
    news = cur.fetchall()
    return render_template('index.html', news=news)


# Отображение свободных мест в реальном времени
@app.route('/real_time')
def real_time():
    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    events = cur.execute(
        'SELECT event.id_evt, event, activity, date, staff_max, classroom_max, COUNT(event.id_evt) FROM event JOIN registration ON event.id_evt = registration.id_evt WHERE date > date("now") GROUP BY event.id_evt'
    ).fetchall()
    events = [(x[1], x[2], x[3], nulling(x[4]) + nulling(x[5]) - nulling(x[6])) for x in events]
    return render_template('real_time.html', events=events)


# О нас
@app.route('/about')
def about():
    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    content = str(cur.execute('SELECT body FROM pages WHERE place = "about"').fetchone()[0])
    conn.close()
    content = content.format(link_reg=url_for('person'))
    return render_template('about.html', content=content)


# Контакты
@app.route('/contact')
def contact():
    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    content = cur.execute('SELECT body FROM pages WHERE place = "contact"').fetchone()[0]
    conn.close()
    return render_template('contact.html', content=content)


# Функция для проверки адресов в бд через js
@app.route('/xxx')
def xxx():
    check_mail = request.args['mail']
    conn = sqlite3.connect('sql/volonteer.db')
    curI = conn.cursor()
    curII = conn.cursor()
    curI.execute('SELECT email FROM person')
    curII.execute('SELECT email FROM temp_user')
    mailsI = curI.fetchall()
    mailsII = curII.fetchall()
    mailI = [i[0] for i in mailsI]
    mailII = [i[0] for i in mailsII]
    return str(check_mail in mailII or check_mail in mailI)


# II Панель администратора - Перенесена в blueprint admin

# III Регистрация личного кабинета - регистрационная форма
@app.route('/person')
def person():
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('SELECT * FROM faculty ORDER BY short_name')
    facultes = cur.fetchall()
    conn.close()
    return render_template('personadd.html', facultes=facultes)


# Регистрация личного кабинета - добавление нового пользователя во временную таблицу и отправка подтверждающего сообщения
@app.route('/personview', methods=['GET', 'POST'])
def personview():
    surname = request.form['surname'].strip().title()
    name = request.form['name'].strip().title()
    patronymic = request.form['patronymic'].strip().title()
    birthday = request.form['birthday']
    faculty = request.form['faculty']
    email = request.form['email']
    phone = request.form['phone']
    login = request.form['login']
    password = request.form['password']
    # получение текущей даты в iso формате
    today = date.today()
    # преобразование даты в строку
    date_reg = str(today)
    sex = request.form['sex']
    year_st = request.form['year_st']
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    # Удаление старых записей во временной таблице по проществии 30 дней с момента регистрации
    cur.execute("SELECT hash, date_reg FROM temp_user")
    for row in cur.fetchall():
        # преобразуем строку из базы в дату и вычитаем ее из текущей, если дельта больше 30 дней, удаляем строку
        if (date.today() - date.fromisoformat(row[1])) > timedelta(30): cur.execute(
            "DELETE FROM temp_user WHERE hash='{}'".format(row[0]))
    # Сохраняем изменения
    conn.commit()

    # генерация случайного числа
    rand = str(random.randint(3245, 6000000))
    # убедимся, что такое число отсутствует во временной таблицы, для его уникальности.
    cur.execute('SELECT hash FROM temp_user')
    sec = [x[0] for x in cur.fetchall()]  # Генерируем список из первых элементов запрошенных строк
    while rand in sec:  # Если сгенерированое число уже есть в таблице, генерируем новое
        rand = str(random.randint(3245, 6000000))

    # Запись переданных в форме данных во временную таблицу индексируя строку случайным числом, на него же будем ссылаться из письма с подтверждением регистрации
    cur.execute(
        "INSERT INTO temp_user (hash, surname, name, patronymic, email, faculty, phone, birthday, login, password, date_reg, sex, year_st) VALUES ('" + rand + "', '" + surname + "', '" + name + "', '" + patronymic + "', '" + email + "', '" + faculty + "', '" + phone + "', '" + birthday + "', '" + login + "', '" + password + "', '" + date_reg + "', '" + sex + "', '" + year_st + "')")

    # Сохраняем изменения
    conn.commit()
    # Закрываем соединение с базой
    conn.close()

    # * Отправка почтового сообщения с подтверждением регистрации пользователю
    # * ссылка со сгенерированным числом, для перезаписи из временной таблицы в таблицу пользователей
    host = request.host_url.split(':')  # парсим адрес хоста
    link = host[0] + ':' + host[
        1] + 'confirm/' + rand  # собираем ссылку из хоста, страницы проверки и случайного числа сгенерированного для пользователя

    mail.to_volunteer(email, link, name)  # функция отправки сообщения из файла mail.py
    return '''<html>
                        <head>
                        <META http-equiv="content-type" content="text/html; charset=windows-1251">
                        <title></title>
                        </head>
                        <body>
                        <script type="text/javascript">
                        var sec=10;
                            function Sec()
                            {
                            document.getElementById("sec").innerHTML=sec;
                            sec--;
                            if(sec==1)
                            {
   	                            location.replace("/")
                            }
                            setTimeout('Sec()',1000);
                            }
                        </script>
                        <noscript>
                        <meta http-equiv="refresh" content="20; /">
                        </noscript>''' + '<span>На ваш почтовый адрес {0} отправлена ссылка для подтверждения регистрации</span><br /><a href="{1}">Вернуться на главную страницу</a>'.format(
        email, url_for('index')) + '''
                            <span style="color:red;font-weight: bold;" id="sec" name="sec">10</span> сек. <br />
                            Если автоматический переход не произошел, воспользуйтесь <a href="/">данной ссылкой</a>.
                        <script type="text/javascript">
                            Sec();
                        </script>
                        </body>
                        </html>'''


# Регистрация личного кабинета - подтверждение регистрации по ссылке с почты
@app.route('/confirm/<hash>')
def confirm(hash):
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # Нахождение записи во временной таблице temp_user по коду в ссылке подтверждения
    cur.execute('SELECT * FROM temp_user WHERE hash="{}"'.format(hash))
    row = cur.fetchone()
    if row == None: return '<span>Ваша ссылка подтверждения не действительна!</span><br /><a href="{}">Вернуться на главную страницу</a>'.format(
        url_for('index'))
    # (Захешировать пароль перед перезаписью - не реализовано!)
    # Перезапись значений в постоянную таблицу person
    cur.execute(
        'INSERT INTO person (surname_prsn, name_prsn, patronymic_prsn, faculty, email, phone, birthday, login, password, date_reg, sex, year_st) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]))
    conn.commit()
    # Удаление записи во временной таблице temp_user по коду в ссылке
    cur.execute('DELETE FROM temp_user WHERE hash="{}"'.format(hash))
    conn.commit()
    conn.close()

    # отправить логин и пароль на почтовый адрес
    mail.send_passw(row[5], row[8], row[9], row[2])
    return redirect(url_for('index'))


# IV Авторизация - Вход в личный кабинет волонтера - Форма авторизации
@app.route('/login')
def login():
    if (session.get('id')):
        if session.get('id') == 'admin':
            return redirect(url_for('administrator.index_adm'))
        else:
            return redirect(url_for('user.cabinet', action='1'))
    return render_template('login.html')


@app.route('/unlogin')
def unlogin():
    if (session.get('id')):
        del session['id']
    return redirect(url_for('index'))


# Восстановление логина и пароля по почте
@app.route('/recovery')
def recovery():
    return render_template('recovery.html', message='')


# Восстановления пароля отправка почты
@app.route('/recovery_send', methods=['GET', 'POST'])
def recovery_send():
    email = request.form.get('email')
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    # Делаем выборку всех записей из таблицы Пользователей
    cur.execute('SELECT login, password FROM person WHERE email = "{0}"'.format(email))
    data_reg = cur.fetchone()

    if (data_reg == None):
        return render_template('recovery.html', message='Указанный адрес в базе данных не найден')
    else:
        mail.send_recovery(email, data_reg[0], data_reg[1])
        return render_template('recovery.html',
                               message='Логин и пароль отправлены на вашу почту! <a href="/login">Войти в личный кабинет</a>')


# Личный кабинет волонтера - Вход - обработка формы
@app.route('/cabinetin', methods=['GET', 'POST'])
def cabinetin():
    # Получаем из формы логин и пароль
    login = request.form['login']
    password = request.form['password']

    # Если вход выполнил администратор
    if checker.pswAdm(login, password):
        # Сохраняем id администратора в сессии
        session['id'] = 'admin'
        # Переходим на страницу отображения ЛК
        return redirect(url_for('administrator.index_adm'))

        # Подключаемся к БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    # Делаем выборку всех записей из таблицы Пользователей
    cur.execute('SELECT * FROM person')
    persons = cur.fetchall()
    # Перебираем записи и ищем совпадение введенных логина и пароля
    for p in persons:
        if (p[8] == login and p[9] == password):
            # Сохраняем id этого пользователя в сессии
            session['id'] = p[0]
            conn.close()
            # Переходим на страницу отображения ЛК
            return redirect(url_for('user.cabinet', action='nextevt'))

    conn.close()

    # Если записи не были найдены возвращаем пользователя на главную страницу.
    return '''<html>
                        <head>
                        <META http-equiv="content-type" content="text/html; charset=windows-1251">
                        <title></title>
                        </head>
                        <body>
                        <script type="text/javascript">
                        var sec=10;
                            function Sec()
                            {
                            document.getElementById("sec").innerHTML=sec;
                            sec--;
                            if(sec==1)
                            {
   	                            location.replace("/")
                            }
                            setTimeout('Sec()',1000);
                            }
                        </script>
                        <noscript>
                        <meta http-equiv="refresh" content="20; /">
                        </noscript><span>Увы, но вы не зарегистрированы!</span><br />
                            <span style="color:red;font-weight: bold;" id="sec" name="sec">10</span> сек. <br />
                            Если автоматический переход не произошел, воспользуйтесь <a href="/">данной ссылкой</a>.
                        <script type="text/javascript">
                            Sec();
                        </script>
                        </body>
                        </html>'''


# Верификация кода со справки
@app.route('/vern')
def vern():
    message = ''
    code = request.args.get('code')
    if code is None:
        code = '4-12-45-2-8'
    else:
        id_evt, _, _, id_prsn, _ = code.split("-")
        conn = sqlite3.connect("sql/volonteer.db")
        cur = conn.cursor()
        cur.execute('SELECT visit FROM registration WHERE id_prsn = ? and id_evt = ?', (id_prsn, id_evt))
        reg = cur.fetchone()
        if (int(reg[0]) if reg is not None else 0) > 0:
            fio = cur.execute('SELECT surname_prsn, name_prsn, patronymic_prsn  FROM person WHERE id_prsn = ?', (id_prsn,)).fetchone()
            evt = cur.execute('SELECT activity, date  FROM event WHERE id_evt = ?', (id_evt,)).fetchone()
            fio = ' '.join(fio)
            message = '{} {} принял(-а) участие в мероприятии «{}» в качестве волонтера'.format(fio, evt[1], evt[0])
        else:
            message = 'Данный код не действителен'
        # Пишем здесь __________________________________________

    return render_template('vern.html', message=message, code=code)


# ------------- test

# @app.route('/test')
# def test():
#     # Подключаемся к БД
#     conn = sqlite3.connect("sql/volonteer.db")
#     cur = conn.cursor()
#
#     # Делаем выборку всех записей из таблицы Пользователей
#     cur.execute("SELECT date FROM event WHERE date(date) > date('now')")
#     persons = cur.fetchall()
#
#     conn.close()
#
#     # Если записи не были найдены возвращаем пользователя на главную страницу.
#     return str(persons)

# ----------------------- Конец скрипта ------------------------ #

if __name__ == '__main__':
    app.run(debug=True)
