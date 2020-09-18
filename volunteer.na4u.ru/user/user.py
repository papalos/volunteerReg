from flask import Blueprint, render_template, request, redirect, url_for, session     # инструменты Flask
import sqlite3                                                                        # для работы с БД SQLite
from datetime import date, timedelta                                                  # класс для работы с датой


cabin = Blueprint('user', __name__, template_folder='templates')


############## Личные кабинеты пользователей ############
# Личный кабинет волонтера - Внешний вид
@cabin.route('/cabinet/<action>')
def cabinet(action):
    # Переменная для сохранения отображаемого на странице контента
    content = ''
    # Подключаемся к базе данных
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # Получаем ФИО пользователя по id записанного в сессию
    cur.execute('SELECT * FROM person WHERE id_prsn={}'.format(session['id']))
    # Сохраняем ФИО в переменную для передачи его в шаблон
    volonteer = cur.fetchone()
    fio = '_'.join(volonteer[1:4])

    if action == 'lastevt':  # отображается когда запрашиваются события которые посетил пользователь
        bold = 3
        # Получаем пересекающиеся данные из таблиц События и Регистрации
        # и выбираем из них только те, которые посетил пользователь с id записанным в сессию
        cur = cur.execute('SELECT event.id_evt, event.event, event.activity, event.date FROM event JOIN registration ON event.id_evt=registration.id_evt WHERE registration.id_prsn={} AND registration.visit =1'.format(session['id']))
        # В переменной Контент формируем таблицу для вывода
        content = '<p>Прошедшие события, в которых вы приняли участие в качестве волонтера</p><table class="table table-striped"><thead><th>Событие</th><th>Активность/Предмет</th><th>Дата</th><th>Справка</th></thead><tbody>'
        # Перебираем все полученные записи
        for row in cur:
            # формируем код подтверждения посещения состоит из id события, даты события, id участника
            a, b, c = row[3].split('-')
            ls = (str(row[0]), str(int(c)), str(int(a)-2010), str(session['id']), str(int(b)))
            code = '-'.join(ls)
            # формируем строки таблицы
            content += '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td><a href="{4}" target="_blank">Получить справку</a></td></tr>'.format(row[1], row[2], row[3], code, url_for('user.gen_pdf', code=code, fio=fio))
        content += '</tbody></table>'
    elif action == 'regevt': # отображается когда запрашиваются события на которые зарегистрирован пользователь
        bold = 2
        # Получаем пересекающиеся данные из таблиц События и Регистрации
        # и выбираем из них только те, на которые зарегистрирован пользователь с id записанным в сессию
        # и время проведения больше или равно текущему
        cur = cur.execute("SELECT event.id_evt, event.event, event.activity, event.date, event.time_in, event.address, registration.role FROM event JOIN registration ON event.id_evt=registration.id_evt WHERE registration.id_prsn={} AND date(date) >= date('now')".format(session['id']))
        # В переменной Контент формируем таблицу для вывода
        content = '<p>Предстоящие события, на которые вы зарегистрированны в качестве волонтера</p><table class="table table-striped"><thead><th>Событие</th><th>Активность/Предмет</th><th>Дата</th><th>Время явки</th><th>Адрес</th><th>Роль</th><th></th></thead><tbody>'
        # Перебираем все полученные записи
        for row in cur:
            # Получаем из ячейки Дата данные и превращаем их в массив разделяя строку по дефисам
            ls = row[3].split('-')
            # объединяем обратно в единую строку и преобразуем в число
            ls = int(''.join(ls))
            # получаем и преобразуем в число текущую дату и сравниваем его с датой события
            crnt = int(''.join((date.today() + timedelta(days=1)).isoformat().split('-')))
            if ls > crnt:
                delreg = '<a href="/us/cancel_registration/{}">Отменить регистрацию</a>'.format(row[0])
            else:
                # если предстоящее событие завтра, отменить регистрацию нельзя, ссылка на отмену регистрации не выводится в таблице
                delreg = ''
            # формируем строки таблицы только из тех событий, даты которых больше текущей даты.
            content += '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>'.format(row[1], row[2], row[3], row[4], row[5], row[6], delreg)
        content += '</tbody></table>'
    else:    # Отображается когда показываются предстоящие события на которые можно зарегистрироваться
        # Выделение жирным вкладки таблицы
        bold = 1

        # Сортировка в столбцах таблицы
        srt = request.args.get('srt')
        if srt == 'event':
            sort = 'event'
        elif srt == 'activity':
            sort = 'activity'
        else:
            sort = 'date DESC'

        # Делаем выборку событий, в которых зарегистрировался пользователь с id сохраненным в сессии из таблицы Регистриция
        # Из таблицы События выбираем события с id_evt  не входящим в первую выборку,
        # т.е. те на которые данный пользователь еще не регистрировался
        cur = cur.execute("SELECT * FROM event WHERE id_evt NOT IN (SELECT id_evt FROM registration WHERE id_prsn ={0}) AND date(date) > date('now') ORDER BY {1}".format(session['id'], sort)).fetchall()
        id_events = tuple(x[0] for x in cur)
        
        # Из таблицы Регистрации выбираем зарегистрированных на это событие и считаем их количество
        # формируем список role_dict вида {18: {'аудитория': 8, 'штаб': 4}, 5: {'аудитория': 1}}
        curII = conn.cursor()
        curII.execute("SELECT id_evt, role FROM registration WHERE id_evt IN {}".format(id_events + tuple('-1'))) #+tuple('-1') передача в кортеже одного элемента вызывает ошибку
        role_dict = {}
        for x in curII:
            if role_dict.get(x[0]):
                if role_dict.get(x[0]).get(x[1]):
                    role_dict[x[0]][x[1]] += 1
                else:
                    role_dict[x[0]][x[1]] = 1
            else:
                role_dict[x[0]] = {x[1]: 1}

        # формируем переменную контент из строк вышеуказанной выборки
        content = '''
            <p>События, доступные для регистрации <br> 
            <span style="color:red">Красным цветом выделены события, регистрация на которые завершена</span>. </br>
            При желании вы можете добавиться в резерв. Если место освободится, вы будете информированы об этом.</br>
            После инфорирования об освободившихся местах вы автоматически удаляетесь из резерва!</p>
            <table class="table table-striped">
                <col width="20%"><col width="20%">
                <col width="15%"><col width="10%">
                <col width="20%"><col width="15%"> 
                <thead>
                    <th><a href="/us/cabinet/nextevt?srt=event">Событие</a></th>
                    <th><a href = "/us/cabinet/nextevt?srt=activity">Активность/Предмет</a></th>
                    <th><a href="/us/cabinet/nextevt">Дата</a></th>
                    <th>Время явки</th>
                    <th>Адрес</th><th></th>
                </thead><tbody>'''
        # Из таблицы События выбираем события с id_evt на которые данный пользователь еще не регистрировался
        for row in cur:
            ls = row[3].split('-')
            ls = int(''.join(ls))
            if ls > int(''.join(date.today().isoformat().split('-'))):
                # Проверяем есть ли свободные места,
                # role_dict содержит количество зарегистрированных на мероприятие по ролям
                if row[10] > role_dict.get(row[0], {}).get('аудитория', 0) or row[8] > role_dict.get(row[0], {}).get('штаб', 0):
                    # Если есть даем возможность зарегистрироваться
                    style = 'style = "color:black;"'
                    reg = '<a href="/us/registration_view/{}">Зарегистрироваться</a>'.format(row[0])
                else:
                    # Иначе проверяем есть ли этот волонтер в резерве
                    style = 'style = "color:red;"'
                    curIII = conn.cursor()
                    curIII.execute("SELECT * FROM reserve WHERE id_evt = {} AND id_prsn = {} LIMIT 1".format(row[0], session['id']))
                    if len(curIII.fetchall()) != 0:
                        # Если есть сообщаем ему об этом
                        reg = '<span>Вы в резерве</span>'
                    else:
                        # Иначе проверяем есть ли свободные места в резерве (ограничим их 10-ю на каждое событие)
                        curIV = conn.cursor()
                        count = curIV.execute("SELECT COUNT(id_evt) FROM reserve WHERE id_evt = {}".format(row[0])).fetchone()[0]
                        if count > 9:
                            # Если нет сообщаем ему об этом
                            reg = '<span>Резерв набран</span>'
                        else:
                            # Иначе есть даем возможность добавиться в резерв
                            reg = '<a href="/us/reserve/{}">Резерв</a>'.format(row[0])
                content += '<tr {style}><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{reg}</td></tr>'.format(row[1], row[2], row[3], row[4], row[11], reg=reg, style=style)
        content += '</tbody></table>'
    # Закрываем БД и выводим шаблон ЛК передавая ФИО пользователя и контент для отображения на странице
    conn.close()
    return render_template('cabinet.html', volonteer=volonteer, content=content, bold=bold)


# Личный кабинет - резервирование на мероприятии
@cabin.route('/reserve/<id_evt>', methods=['GET', 'POST'])
def reserve(id_evt):
    if session.get('id') is None:
        return 'Ошибка идентификации вернитесь на <a href="{}">главную страницу</a>'.format(url_for('index'))
    conn = sqlite3.connect("sql/volonteer.db")    
    cur = conn.cursor()
    curI = conn.cursor()
    row = cur.execute('SELECT id_prsn, email FROM person WHERE id_prsn={}'.format(session['id'])).fetchone()
    curI.execute('INSERT INTO reserve (id_evt, id_prsn, email) VALUES (?, ?, ?)', (id_evt, row[0], row[1]))
    conn.commit()
    conn.close()
    return redirect(url_for('user.cabinet', action='nextevt'))


# Личный кабинет - регистрация пользователя на событие внешний вид
@cabin.route('/registration_view/<id_evt>', methods=['GET', 'POST'])
def registration_view(id_evt):
    if session.get('id') is None:
        return 'Ошибка идентификации вернитесь на <a href="{}">главную страницу</a>'.format(url_for('index'))
    conn = sqlite3.connect("sql/volonteer.db")
    curI = conn.cursor()
    curII = conn.cursor()
    currIII = conn.cursor()
    
    # Получаем ФИО пользователя по id записанного в сессию
    curI.execute('SELECT * FROM person WHERE id_prsn={}'.format(session['id']))
    # Получаем данные о событии по его id
    curII.execute('SELECT * FROM event WHERE id_evt={}'.format(id_evt))
    # Количество регистраций на определенное событие по его id
    currIII.execute('SELECT role FROM registration WHERE id_evt={}'.format(id_evt))
    # Сохраняем ФИО в переменную для передачи его в шаблон
    volonteer = curI.fetchone()
    event = curII.fetchone()
    num_evt = [x[0] for x in currIII.fetchall()]
    num_staff = num_evt.count('штаб')
    num_classroom = num_evt.count('аудитория')
    
    conn.close()

    return  render_template('registration_view.html', volonteer=volonteer, event=event, num_staff = num_staff, num_classroom = num_classroom)


# Личный кабинет - регистрация пользователя на событие
@cabin.route('/registration', methods=['GET', 'POST'])
def registration():
    role = request.form.get('role')
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # Вставка записи в таблицу регистраций
    cur.execute("INSERT INTO registration (id_prsn, id_evt, role) VALUES ('" +str(session['id'])+ "', '" +request.form.get('id_evt')+ "', '" +role+ "')")
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    return redirect(url_for('user.cabinet', action='nextevt'))


# Личный кабинет - Отмена регистрации пользователя на событие
@cabin.route('/unregistration/<id_evt>', methods=['GET', 'POST'])
def unregistration(id_evt):
    # Соединение с БД
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # Удаление записи в таблицу регистраций
    cur.execute("DELETE FROM registration WHERE id_prsn={} AND id_evt = {}".format(str(session['id']), id_evt))
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    return redirect(url_for('user.cabinet', action='regevt'))


# Личный кабинет - Отмена регистрации пользователя на событие
@cabin.route('/cancel_registration/<id_evt>', methods=['GET', 'POST'])
def cancel_registration(id_evt):
    return render_template("cancel_registration.html", id_evt=id_evt)


# Генерирует pdf со справкой
@cabin.route('/gen_pdf/<code>/<fio>')
def gen_pdf(code, fio):
    id_evt, day, year, id_user, month = code.split("-")
    evt_date = '{:02d}.{:02d}.{}'.format(int(day), int(month), int(year)+2010)
    fio = ' '.join(fio.replace('_-', ' ').split('_'))
    conn = sqlite3.connect("sql/volonteer.db")
    cur = conn.cursor()
    # Получаем ФИО пользователя по id записанного в сессию
    activity_name = cur.execute('SELECT activity FROM event WHERE id_evt=?', (id_evt,)).fetchone()[0]

    return render_template('generate_pdf.html', fio=fio, evt_date=evt_date, code=code, activity_name=activity_name)
