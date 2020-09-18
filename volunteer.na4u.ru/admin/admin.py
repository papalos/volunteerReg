from flask import Blueprint, render_template, request, redirect, url_for, session, send_file     # инструменты Flask
import sqlite3                                                                    # для работы с БД SQLite
from datetime import date                                                         # класс для работы с датой
import mail                                                                       # отправка сообщения для подтверждения регистрации
import xlsxwriter                                                                 # создание документа .xmlx


FOR_TABLE = ('Номер_события', 'Событие', 'Активность', 'Дата _проведения', 'Время начала', 'Продолжительность', 'Адрес проведения', 'Номер_волонтера', 'Фамилия', 'Имя', 'Отчество', 'Факультет', 'e-mail', 'Телефон', 'Дата_рождения', 'Пол', 'Курс', 'Отметка_о_посещении', 'Роль выбраная при регистрации', 'Аудитория')
FOR_TABLE_ALLUSERS = ('id', 'Фамилия', 'Имя', 'Отчество', 'Факультет', 'e-mail', 'Телефон', 'Дата рожедния', 'Логин', 'Пароль' , 'Дата регистрации', 'Пол', 'Курс')
FOR_TABLE_SOMEEVENTS = ('id', 'Событие', 'Активность', 'Дата проведения', 'Время прихода', 'Время начала', 'Продолжительность', 'Штаб_min', 'Штаб_max', 'Аудитория_min', 'Аудитория_max', 'Адресс')
FOR_TABLE_USERREGISTERONEVENT = ('id', 'Фамилия', 'Имя', 'Отчество', 'Факультет', 'e-mail', 'Телефон', 'День рождения', 'Роль')
FOR_TABLE_USERVISIT = ('id', 'Фамилия', 'Имя', 'Отчество', 'Факультет', 'e-mail', 'Телефон', 'Дата рождения', 'Пол', 'Курс', 'Аудитория')
PAGE_ERROR_ENTER = '''<html>
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
                        <meta http-equiv="refresh" content="20; /admin/faculty">
                        </noscript>
                        Доступ закрыт. Войдите как администратор!<br />
                        Возврат на главную страницу через: 
                            <span style="color:red;font-weight: bold;" id="sec" name="sec">10</span> сек. <br />
                            Если автоматический переход не произошел, воспользуйтесь <a href="/">данной ссылкой</a>.
                        <script type="text/javascript">
                            Sec();
                        </script>
                        </body>
                        </html>'''

panel = Blueprint('administrator', __name__, template_folder='templates')


# Панель администратора
# Управление пользователями
@panel.route('/')
def index_adm():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    return render_template('admn.html')


# Панель администратора (пользователь) - все пользователи (выводит всех пользователей из постоянной таблицы person
@panel.route('/allusers')
def allusers():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('''SELECT p.*, r.num, t.num
                   FROM person AS p 
                   LEFT JOIN (SELECT id_prsn, COUNT(visit) AS num FROM registration GROUP BY id_prsn) AS r ON p.id_prsn = r.id_prsn
                   LEFT JOIN (SELECT id_prsn, COUNT(visit) AS num FROM registration WHERE visit=1 GROUP BY id_prsn) AS t ON p.id_prsn = t.id_prsn
                ''')
    persons = cur.fetchall()
    conn.close()
    return render_template('allusers.html', persons=persons)


# Панель администратора (без регистрации)
# - не завершившие регистрацию (выводит всех пользователей из временной таблицы temp_user)
@panel.route('/tempusers')
def tempusers():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('SELECT * FROM temp_user')
    persons = cur.fetchall()
    conn.close()
    return render_template('tempusers.html', persons=persons)


# Регистрация личного кабинета от имени администратора
@panel.route('/confirm_adm/<hash>')
def confirm_adm(hash):
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # Нахождение записи во временной таблице temp_user по коду в ссылке подтверждения
    cur.execute('SELECT * FROM temp_user WHERE hash="{}"'.format(hash))
    row = cur.fetchone()
    if row == None: return '<span>Данный пользователь не обнаружен!</span><br /><a href="{}">Вернуться к временной таблице</a>'.format(url_for('administrator.tempusers'))
    # Перезапись значений в постоянную таблицу person
    cur.execute('INSERT INTO person (surname_prsn, name_prsn, patronymic_prsn, faculty, email, phone, birthday, login, password, date_reg, sex, year_st) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}", "{9}", "{10}", "{11}")'.format(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]))
    conn.commit()
    # Удаление записи во временной таблице temp_user по коду в ссылке
    cur.execute('DELETE FROM temp_user WHERE hash="{}"'.format(hash))
    conn.commit()
    conn.close()

    # отправить логин и пароль на почтовый адрес
    mail.send_passw(row[5], row[8], row[9], row[2])    
    return redirect(url_for('administrator.tempusers'))


# Панель администратора (пользователь) - удаляет пользователя из постоянной таблицы person
@panel.route('/deluser')
def deluser():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    del_num = request.args.get('idu')
    cur.execute('DELETE FROM person WHERE id_prsn = {}'.format(del_num))
    cur.execute('DELETE FROM registration WHERE id_prsn = {}'.format(del_num))
    conn.commit()
    conn.close()
    return redirect(url_for('administrator.allusers'))


# Открытие на редактирование данных указанного пользователя 
@panel.route('/editperson/<id>')
def editperson(id):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM person WHERE id_prsn = ?", (id,))
    result=cur.fetchone()
    return render_template('personedit.html', result=result)


# Сохранение в БД отредактированных данных пользователя
@panel.route('/setedit', methods=['GET','POST'])
def setedit():
    id = request.form['id']
    surname = request.form['surname']
    name = request.form['name']
    patronymic = request.form['patronymic']
    birthday = request.form['birthday']
    faculty = request.form['faculty']
    email = request.form['email']
    phone = request.form['phone']
    login = request.form['login']
    password = request.form['password']
    sex = request.form['sex']

    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    # Удаление старых записей во временной таблице по проществии 30 дней с момента регистрации
    cur.execute("UPDATE person SET surname_prsn = ?, name_prsn = ?, patronymic_prsn=?, faculty=?, email=?, phone=?, birthday=?, login=?, password=?, sex=? WHERE id_prsn = ?",(surname, name, patronymic, faculty, email, phone, birthday, login, password, sex, id))
    
    conn.commit()
    conn.close()
   
    return redirect(url_for('administrator.index_adm'))


# Форма дорегистрации пользователя на событие 
@panel.route('/extraregistration/<id>')
def extraregistration(id):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    curI = conn.cursor()
    curII = conn.cursor()

    curI.execute("SELECT * FROM person WHERE id_prsn = ?", (id,))
    curII.execute("SELECT id_evt FROM event")
    result = curI.fetchone()
    evts = curII.fetchall()
    return render_template('extraregistration.html', result=result, evts=evts)


# Сохранение в БД сведений о дорегистрации пользователя
@panel.route('/extraregsave', methods=['GET','POST'])
def extraregsave():
    id_prsn = request.form['id_prsn']
    id_evt = request.form['id_evt']
    role = request.form['role']
    classroom = request.form['classroom']

    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    # Удаление старых записей во временной таблице по проществии 30 дней с момента регистрации
    cur.execute("INSERT INTO registration VALUES (?,?,1,?,?)",(id_prsn, id_evt, role, classroom))
    
    conn.commit()
    conn.close()
   
    return redirect(url_for('administrator.index_adm'))


# Просмотр таблицы резервистов
@panel.route('/reserve')
def reserve():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    res = cur.execute("SELECT date, event, activity, id_prsn, email, reserve.id_evt FROM reserve JOIN event ON reserve.id_evt = event.id_evt").fetchall()
    conn.close()
    return render_template('/reserve.html', res=res)

# Удаление из таблицы резервистов
@panel.route('/reservedel/<evt>/<prs>')
def reservedel(evt, prs):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM reserve WHERE id_evt=? and id_prsn=?", (evt, prs))
    conn.commit()
    conn.close()
    return redirect(url_for('administrator.reserve'))


# Просмотр текста страниц
@panel.route('/pages')
def pages():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    text = cur.execute("SELECT * FROM pages").fetchall()
    conn.close()
    return render_template('/text_page.html', text=text)


# Изменения страниц и рассылок
@panel.route('/change_page', methods=['GET','POST'])
def change_page():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    place = request.form.get('place')
    theme = request.form.get('theme')
    body = request.form.get('body')

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('UPDATE pages SET theme = ?, body = ? WHERE place = ?', (theme, body, place))
    conn.commit()
    conn.close()
    return redirect(url_for('administrator.pages'))


# ----------------------------- Раздел с событиями -----------------------------------------------

# Панель администратора (события) - выводит список всех событий
@panel.route('/event')
def event():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    # Сортировка в столбцах таблицы
    srt = request.args.get('srt')
    if srt == 'event':
        sort = 'event'
    elif srt == 'activity':
        sort = 'activity'
    else:
        sort = 'date DESC'

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('SELECT * FROM event ORDER BY {0}'.format(sort))
    events = cur.fetchall()
    conn.close()
    return render_template('event.html', events=events)


# Панель администратора (события) - выводит список всех событий
@panel.route('/event_add_html')
def event_add_html():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    return render_template('event_add_html.html')


# Панель администратора (события) - выполняет добавление нового события и редирект к списку всех событий
@panel.route('/eventadd', methods=['GET', 'POST'])
def eventadd():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    event = request.form['event']
    activity = request.form['activity']
    date = request.form['date']
    time_in = request.form['time_in']
    time_start = request.form['time_start']
    duration = request.form['duration']
    staff_min = request.form['staff_min']
    staff_max = request.form['staff_max']
    classroom_min = request.form['classroom_min']
    classroom_max = request.form['classroom_max']
    address = request.form['address']

    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    # Вставка записи в таблицу событий
    cur.execute("INSERT INTO event (event, activity, date, time_in, time_start, duration, staff_min, staff_max, classroom_min, classroom_max, address) VALUES ('" +event+ "', '" +activity+ "', '" +date+ "', '" +time_in+ "', '" +time_start+ "', '" +duration+ "', '" +staff_min+ "', '" +staff_max+ "', '" +classroom_min+ "', '" +classroom_max+ "', '" +address+ "')")

    # Фиксируем изменения в базе
    conn.commit()    

    # Закрываем соединение
    conn.close()
    
    return redirect(url_for('administrator.event'))


# Панель администратора (события) - удаление события и редирект к списку событий
@panel.route('/deletevt/<id>')
def deletevt(id):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # Удаляем запись из таблицы событий
    cur.execute("DELETE FROM event WHERE id_evt = '{}'".format(id))
    # Удаляем запись из таблицы регистраций на событие
    cur.execute("DELETE FROM registration WHERE id_evt = '{}'".format(id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('administrator.event'))


# Панель администратора (события) - редактирование события
@panel.route('/changevt/<id>')
def changevt(id):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()    
    cur.execute("SELECT * FROM event WHERE id_evt = '{}'".format(id))
    test_str = cur.fetchone()
    conn.close()
    
    return render_template('event_change_html.html', event=test_str)


# Панель администратора (события) - установка изменений в событии
@panel.route('/eventsetchng', methods=['GET', 'POST'])
def eventsetchng():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    id = request.form['id']
    event = request.form['event']
    activity = request.form['activity']
    date = request.form['date']
    time_in = request.form['time_in']
    time_start = request.form['time_start']
    duration = request.form['duration']
    staff_min = request.form['staff_min']
    staff_max = request.form['staff_max']
    classroom_min = request.form['classroom_min']
    classroom_max = request.form['classroom_max']
    address = request.form['address']

    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()    
    # Вставка записи в таблицу событий
    cur.execute("UPDATE event SET event=?, activity=?, date=?, time_in=?, time_start=?, duration=?, staff_min=?, staff_max=?, classroom_min=?, classroom_max=?, address=? WHERE id_evt=?", (event,activity,date,time_in,time_start,duration,staff_min,staff_max,classroom_min,classroom_max,address,id))
    # Фиксируем изменения в базе
    conn.commit()    
    # Закрываем соединение
    conn.close()
    
    return redirect(url_for('administrator.event'))


# Панель администратора (события) - статистика регистраций на событие, списки волонтеров зарегистрировавшихся на конкретное событие
@panel.route('/stat/<id_evt>')
def stat(id_evt):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    conn = sqlite3.connect("sql/volonteer.db")
    curI = conn.cursor()
    curII = conn.cursor()
    # Выборка волонтеров зарегистрированных на конкретное событие
    curI.execute("SELECT p.id_prsn, surname_prsn, name_prsn, patronymic_prsn, faculty, email, phone, birthday, r.role, r.visit, r.classroom FROM registration AS r JOIN person AS p ON r.id_prsn=p.id_prsn WHERE r.id_evt = {} ORDER BY surname_prsn".format(id_evt))
    # Данные о событии по его id
    curII.execute("SELECT * FROM event WHERE id_evt = {}".format(id_evt))
    registration = curI.fetchall()
    x_count = [x[8] for x in registration]
    x_staff = x_count.count('штаб')
    x_classroom = x_count.count('аудитория')
    event = curII.fetchone()
    
    conn.close()

    return render_template('stat.html', registration=registration, event=event, x_staff=x_staff, x_classroom=x_classroom, id_evt=id_evt)


# Панель администратора (события)
# - статистика регистраций на событие, списки волонтеров зарегистрировавшихся на конкретное событие
@panel.route('/visit/<id_evt>')
def visit(id_evt):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    conn = sqlite3.connect("sql/volonteer.db")
    curI = conn.cursor()
    curII = conn.cursor()
    # Выборка волонтеров зарегистрированных на конкретное событие
    curI.execute("SELECT p.id_prsn, surname_prsn, name_prsn, patronymic_prsn, faculty, email, phone, birthday, sex, year_st, classroom FROM registration AS r JOIN person AS p ON r.id_prsn=p.id_prsn WHERE r.id_evt = {} AND visit=1".format(id_evt))
    # Данные о событии по его id
    curII.execute("SELECT * FROM event WHERE id_evt = {}".format(id_evt))
    visited = curI.fetchall()
    count = len(visited)
    event = curII.fetchone()

    return render_template('visit.html', visited=visited, event=event, count=count, id_evt=id_evt)


# Панель администратора (события) - отметить волонтера на событии
@panel.route('/check', methods=['GET', 'POST'])
def check():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
   
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()

    event = request.form['event']
    _form = request.form
    print(_form)
    ls = _form.getlist('list')
    print(ls)

    for key in ls:
        if _form.get(key) == 'on':
            # Меняем нолик на единицу в таблице регистраций,
            # устанавливая посещение волонтером с id = key мероприятия с id = event
            cur.execute("UPDATE registration SET visit = 1, classroom='{2}' WHERE id_prsn = {0} AND id_evt={1}".format(key, event, _form.get('classroom_for_'+key)))
        else:
            cur.execute("UPDATE registration SET visit = 0, classroom='{2}' WHERE id_prsn = {0} AND id_evt={1}".format(key, event, _form.get('classroom_for_' + key)))
        conn.commit()

    conn.close()    
    return redirect(url_for('administrator.event'))


# ------------------------------------- Раздел о факультетах -----------------------------------------------------------

# Форма для информации о факультетах
@panel.route('/faculty')
def faculty():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('SELECT * FROM faculty ORDER BY full_name')
    faculty = cur.fetchall()
    conn.close()

    return render_template('faculty.html', faculty=faculty)


# Добавления факультета
@panel.route('/facultyadd', methods=['GET', 'POST'])
def facultyadd():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    full_name = request.form.get('full_name')
    short_name = request.form.get('short_name')
    leader_name = request.form.get('leader_name')
    phone = request.form.get('phone')
    email = request.form.get('email')

    conn = sqlite3.connect("sql/volonteer.db")
    # Проверка создаваемого факультета на уникальность
    cur0 = conn.cursor()
    cur0.execute('SELECT full_name, short_name FROM faculty')
    listFaculty = cur0.fetchall()
    for i in listFaculty:
        if full_name in i or short_name in i:
            return '''<html>
                        <head>
                        <META http-equiv="content-type" content="text/html; charset=windows-1251">
                        <title></title>
                        </head>
                        <body>
                        <script type="text/javascript">
                        var sec=20;
                            function Sec()
                            {
                            document.getElementById("sec").innerHTML=sec;
                            sec--;
                            if(sec==1)
                            {
   	                            location.replace("/admin/faculty")
                            }
                            setTimeout('Sec()',1000);
                            }
                        </script>
                        <noscript>
                        <meta http-equiv="refresh" content="20; /admin/faculty">
                        </noscript>
                        Найдено совпадение с записью в базе данных. <br />
                        Не создавайте похожих записей. <br />
                        Воспользуйтесь функцией редактирования записи. <br />
                        Возврат к предыдущей страницы произойдет через: 
                            <span style="color:red;font-weight: bold;" id="sec" name="sec">10</span> сек. <br />
                            Если автоматический переход не произошел воспользуйтесь 
                            <a href="/admin/faculty">данной ссылкой</a>
                        <script type="text/javascript">
                            Sec();
                        </script>
                        </body>
                        </html>'''
    cur = conn.cursor()
    cur.execute('INSERT INTO faculty (full_name, short_name, leader_name, phone, email) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}")'.format(full_name, short_name, leader_name, phone, email))
    conn.commit()
    conn.close()

    return redirect(url_for('administrator.faculty'))


# Удаление факультета
@panel.route('/facultydel/<f_id>')
def facultydel(f_id):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('DELETE FROM faculty WHERE f_id="{}"'.format(f_id))
    conn.commit()
    conn.close()

    return redirect(url_for('administrator.faculty'))


# Форма редактирования факультета
@panel.route('/facultyedit/<f_id>')
def facultyedit(f_id):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn=sqlite3.connect("sql/volonteer.db")
    cur=conn.cursor()
    cur.execute('SELECT * FROM faculty WHERE f_id="{}"'.format(f_id))
    fac = cur.fetchone()
    conn.close()

    return render_template('faculty_edit.html', fac=fac)


# Функция редактирования факультета
@panel.route('/facultyeditfoo', methods=['GET', 'POST'])
def facultyeditfoo():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    f_id = request.form.get('f_id')
    full_name = request.form.get('full_name')
    short_name = request.form.get('short_name')
    leader_name = request.form.get('leader_name')
    phone = request.form.get('phone')
    email = request.form.get('email')

    conn = sqlite3.connect("sql/volonteer.db")

    cur = conn.cursor()
    cur.execute('UPDATE faculty SET full_name = "{0}", short_name = "{1}", leader_name = "{2}", phone = "{3}", email = "{4}" WHERE f_id = "{5}"'.format(full_name, short_name, leader_name, phone, email, f_id))
    conn.commit()
    conn.close()

    return redirect(url_for('administrator.faculty'))


# --------------- Блок новостей -------------------------------------------------------------------------

# Форма для новости
@panel.route('/post')
def post():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn=sqlite3.connect("sql/volonteer.db")
    cur=conn.cursor()
    cur.execute('SELECT * FROM news ORDER BY date DESC')
    news = cur.fetchall()
    conn.close()

    return render_template('posts.html', news=news)


# Публикация новости
@panel.route('/addpost', methods=['GET', 'POST'])
def addpost():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    title = request.form.get('titlepost')
    body = request.form.get('bodypost')
    type = request.form.get('type')    

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('INSERT INTO news (date, title, body, type) VALUES (?,?,?,?)', (date.today(), title, body, type))
    conn.commit()
    conn.close()
    return redirect(url_for('administrator.post'))


# Редактирование новости интерфейс
@panel.route('/postrecovery/<id_new>')
def postrecovery(id_new):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn=sqlite3.connect("sql/volonteer.db")
    cur=conn.cursor()
    cur.execute('SELECT * FROM news WHERE id="{}"'.format(id_new))
    new = cur.fetchone()
    conn.close()
    return render_template('post_recovery.html', new=new)


# Редактирование новости обработка формы
@panel.route('/postrecoveryfoo', methods=['GET','POST'])
def postrecoveryfoo():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    id = request.form.get('id_new')
    date = request.form.get('date')
    title = request.form.get('titlepost')
    body = request.form.get('bodypost')
    type = request.form.get('type')    
    
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('UPDATE news SET date=?, title=?, body=?, type=? WHERE id = ?', (date, title, body, type, id))
    conn.commit()
    conn.close()
    return redirect(url_for('administrator.post'))


# Удаление новости
@panel.route('/delpost/<id_new>')
def delpost(id_new):
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn=sqlite3.connect("sql/volonteer.db")
    cur=conn.cursor()
    cur.execute('DELETE FROM news WHERE id = "{}"'.format(id_new))
    conn.commit()
    conn.close()
    return redirect(url_for('administrator.post'))


# ---------------------------------------- Отчеты --------------------------------------------------------------

# Выгружает всех зарегистрированных пользователей в виде excel файла
@panel.route('/getdata', methods=['GET', 'POST'])
def getdata():
    # является ли пользователь администратором
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect('sql/volonteer.db')
    cur = conn.cursor()
    _since = request.form.get('since')
    _to = request.form.get('to')
    if _since is None and _to is None:
        cur.execute('''SELECT ev.id_evt, ev.event, ev.activity, ev.date, ev.time_start,  ev.duration, ev.address, p.id_prsn, p.surname_prsn, p.name_prsn, p.patronymic_prsn, p.faculty, p.email, p.phone, p.birthday, p.sex, p.year_st, reg.visit, reg.role, reg.classroom
                   FROM registration AS reg 
                   JOIN person AS p ON reg.id_prsn = p.id_prsn
                   JOIN event AS ev ON reg.id_evt = ev.id_evt
                   ORDER BY ev.id_evt DESC''')
    else:
        cur.execute('''SELECT ev.id_evt, ev.event, ev.activity, ev.date, ev.time_start,  ev.duration, ev.address, p.id_prsn, p.surname_prsn, p.name_prsn, p.patronymic_prsn, p.faculty, p.email, p.phone, p.birthday, p.sex, p.year_st, reg.visit, reg.role, reg.classroom
                   FROM registration AS reg 
                   JOIN person AS p ON reg.id_prsn = p.id_prsn
                   JOIN event AS ev ON reg.id_evt = ev.id_evt
                   WHERE ev.date >= '{0}' AND ev.date <= "{1}"
                   ORDER BY ev.id_evt DESC'''.format(_since, _to))
    all = cur.fetchall()
    length = len(all)

    # Создаем книку и лист.
    workbook = xlsxwriter.Workbook('registr.xlsx')
    worksheet = workbook.add_worksheet()
    
    # Заносим данные в таблицу
    row = 0
    col = 0
    for h in FOR_TABLE:
        worksheet.write(row, col, h)
        col += 1
    row += 1
    for item in all:
        col = 0
        for element in item:
            worksheet.write(row, col, element)
            col += 1
        row += 1

    worksheet.write(row, 0, date.today().strftime("%Y-%m-%d %H:%M:%S"))

    workbook.close()

    try:
        send = send_file('registr.xlsx', cache_timeout=0, attachment_filename='registr.xlsx', as_attachment=True)
    except:
        send = 'Ошибка создания файла!'
    finally:
        conn.close()
    return send


# Выгружает всех зарегистрированных пользователей
@panel.route('/getallusers')
def getallusers():
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('SELECT * FROM person')
    persons = cur.fetchall()
    length = len(persons)

    # Создаем книку и лист.
    workbook = xlsxwriter.Workbook('allusers.xlsx')
    worksheet = workbook.add_worksheet()
    
    # Заносим данные в таблицу
    row = 0
    col = 0
    for h in FOR_TABLE_ALLUSERS:
        worksheet.write(row, col, h)
        col += 1
    row += 1
    for item in persons:
        col = 0
        for element in item:
            worksheet.write(row, col, element)
            col += 1
        row += 1

    worksheet.write(row, 0, date.today().strftime("%Y-%m-%d %H:%M:%S"))

    workbook.close()

    try:
        send = send_file('allusers.xlsx', cache_timeout=0, attachment_filename='allusers.xlsx', as_attachment=True)
    except:
        send='Ошибка создания файла!'
    finally:
        conn.close()
    return send


# Выгружает события по заданным срокам
@panel.route('/getsomeevents', methods=['GET', 'POST'])
def getsomeevents():
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    _since = request.form.get('since')
    _to = request.form.get('to')

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('SELECT * FROM event WHERE date >= "{0}" AND date <= "{1}"'.format(_since, _to))
    someevents = cur.fetchall()
    length = len(someevents)

    # Создаем книку и лист.
    workbook = xlsxwriter.Workbook('someevents.xlsx')
    worksheet = workbook.add_worksheet()
    
    # Заносим данные в таблицу
    row = 0
    col = 0
    for h in FOR_TABLE_SOMEEVENTS:
        worksheet.write(row, col, h)
        col += 1
    row += 1
    for item in someevents:
        col = 0
        for element in item:
            worksheet.write(row, col, element)
            col += 1
        row += 1

    worksheet.write(row, 0, date.today().strftime("%Y-%m-%d %H:%M:%S"))

    workbook.close()

    try:
        send = send_file('someevents.xlsx', cache_timeout=0, attachment_filename='someevents.xlsx', as_attachment=True)
    except:
        send = 'Ошибка создания файла!'
    finally:
        conn.close()
    return send


# Просмотр динамики регистрации на события по заданным срокам
@panel.route('/scopereg', methods=['GET', 'POST'])
def scopereg():
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    _since = request.form.get('since')
    _to = request.form.get('to')

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute('SELECT * FROM event JOIN (SELECT id_evt, role, COUNT(id_prsn) AS num FROM registration WHERE id_evt IN (SELECT id_evt FROM event WHERE date >= "{0}" AND date <= "{1}") GROUP BY id_evt, role) AS tab ON event.id_evt=tab.id_evt ORDER BY event.id_evt'.format(_since, _to))
    someevents = cur.fetchall()
  
    return render_template("scope.html", someevents=someevents)


# Выгружает зарегистрированных пользователей по конкретному событию
@panel.route('/getuserregistronevent/<id_evt>', methods=['GET', 'POST'])
def getuserregistronevent(id_evt):
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute("SELECT p.id_prsn, surname_prsn, name_prsn, patronymic_prsn, faculty, email, phone, birthday, r.role FROM registration AS r JOIN person AS p ON r.id_prsn=p.id_prsn WHERE r.id_evt = {} ORDER BY surname_prsn".format(id_evt))
    userregistronevent = cur.fetchall()
    length = len(userregistronevent)

    # Создаем книку и лист.
    workbook = xlsxwriter.Workbook('userregistronevent.xlsx')
    worksheet = workbook.add_worksheet()
    
    # Заносим данные в таблицу
    row = 0
    col = 0
    for h in FOR_TABLE_USERREGISTERONEVENT:
        worksheet.write(row, col, h)
        col += 1
    row += 1
    for item in userregistronevent:
        col = 0
        for element in item:
            worksheet.write(row, col, element)
            col += 1
        row += 1

    worksheet.write(row, 0, date.today().strftime("%Y-%m-%d %H:%M:%S"))

    workbook.close()

    try:
        send = send_file('userregistronevent.xlsx', cache_timeout=0, attachment_filename='userregistronevent.xlsx', as_attachment=True)
    except:
        send = 'Ошибка создания файла!'
    finally:
        conn.close()
    return send


# Выгружает посетивших конкретное событие
@panel.route('/getvisit/<id_evt>', methods=['GET', 'POST'])
def getvisit(id_evt):
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER

    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    cur.execute("SELECT p.id_prsn, surname_prsn, name_prsn, patronymic_prsn, faculty, email, phone, birthday, sex, year_st, classroom FROM registration AS r JOIN person AS p ON r.id_prsn=p.id_prsn WHERE r.id_evt = {} AND visit=1".format(id_evt))
    uservisit = cur.fetchall()
    length = len(uservisit)

    # Создаем книку и лист.
    workbook = xlsxwriter.Workbook('uservisit.xlsx')
    worksheet = workbook.add_worksheet()
    
    # Заносим данные в таблицу
    row = 0
    col = 0
    for h in FOR_TABLE_USERVISIT:
        worksheet.write(row, col, h)
        col += 1
    row += 1
    for item in uservisit:
        col = 0
        for element in item:
            worksheet.write(row, col, element)
            col += 1
        row += 1

    worksheet.write(row, 0, date.today().strftime("%Y-%m-%d %H:%M:%S"))

    workbook.close()

    try:
        send = send_file('uservisit.xlsx', cache_timeout=0, attachment_filename='uservisit.xlsx', as_attachment=True)
    except:
        send='Ошибка создания файла!'
    finally:
        conn.close()
    return send


# Выгружает файл базы данных
@panel.route('/backupdb')
def backupdb():
    if session.get('id') != 'admin':
        return PAGE_ERROR_ENTER
    return send_file('sql/volonteer.db', cache_timeout=0, attachment_filename='volonteer.db', as_attachment=True)
