from flask import Flask, g, render_template, send_file, request, redirect, url_for, jsonify
import sqlite3
import traceback
import io
import sys
import os

app = Flask(__name__)
DATABASE = 'databasa.sqlite'
print('asdasdasdasdqsd')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.route('/')
def index():
    # Пример передачи переменной Python в HTML
    my_variable = "Привет, это переменная из Python!"
    return render_template('index.html', my_variable=my_variable)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mail = request.form.get('mail')
        password = request.form.get('password')

        if mail == 'admin' and password == 'admin':
            return redirect("/admin")  # Переход на страницу администратора

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_info WHERE mail = ? AND password = ?', (mail, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return render_template('welcome.html', user=user)
        else:
            return render_template('error.html', message='Invalid credentials')

    return render_template('login.html')


@app.route('/submit', methods=['POST'])
def submit():
    # Получение данных из формы
    user_input = request.form['user_input']
    
    # Пример обработки данных
    processed_data = f"Вы ввели: {user_input}"
    
    # Возвращаем результат обработки данных обратно в HTML
    return render_template('index.html', processed_data=processed_data)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Получаем данные из формы
        name = request.form.get('name')
        mail = request.form.get('mail')
        password = request.form.get('password')

        # Подключаемся к базе данных
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Вставляем данные в таблицу
        cursor.execute('INSERT INTO user_info (name, mail, password) VALUES (?, ?, ?)', (name, mail, password))
        
        # Сохраняем изменения
        conn.commit()

        # Закрываем соединение
        conn.close()

        # Перенаправляем пользователя на главную страницу или другую страницу по вашему выбору
        return render_template('main.html')


@app.route('/tutor')
def open_tutor():
    return render_template('tutorial.html')


@app.route('/admin', methods=['GET', 'POST'])
def openadmintable():
    conn = sqlite3.connect('new_teachers.sqlite')
    cursor = conn.cursor()

    # Запрос данных из таблицы application
    cursor.execute("SELECT * FROM application")
    rows = cursor.fetchall()
    # Запрос данных из таблицы wait
    cursor.execute("SELECT * FROM wait")
    waits = cursor.fetchall()

    # Преобразование данных в список
    applications_list = []
    waiting_list = []

    if request.method == 'POST':
        application_id = request.form['application_id']
        for key in request.form:
            if key.startswith('approve_'):
                # Обработка одобрения заявки по application_id
                # Добавление пользователя в таблицу wait
                cursor.execute("INSERT INTO wait SELECT * FROM application WHERE id = ?", (application_id,))
                # Удаление заявки из таблицы application
                cursor.execute("DELETE FROM application WHERE id = ?", (application_id,))
                print('ПРИНЯТ')
            elif key.startswith('reject_'):
                # Обработка отклонения заявки по application_id
                # Удаление заявки из таблицы application
                cursor.execute("DELETE FROM application WHERE id = ?", (application_id,))
                print('НЕ ПРИНЯТ')
            elif key.startswith('accept_'):
                # Обработка одобрения заявки по application_id
                cursor.execute("SELECT * FROM wait WHERE id = ?", (application_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO wait SELECT * FROM wait WHERE id = ?", (application_id,))
                cursor.execute("DELETE FROM wait WHERE id = ?", (application_id,))
                print('ОКОНЧАТЕЛЬНО ПРИНЯТ')

        conn.commit()

    for row in rows:
        application = {
            'id': row[0],
            'teacher_name': row[1],
            'mail': row[2],
            'phone_number': row[3],
            'shirt_info': row[4]
        }
        if all(value for value in application.values()):
            applications_list.append(application)
        else:
            # Удаление пустой заявки из базы данных
            cursor.execute("DELETE FROM application WHERE id = ?", (row[0],))
            conn.commit()

    for i in waits:
        waiting = {
            'id': i[0],
            'teacher_name': i[1],
            'mail': i[2],
            'phone_number': i[3],
            'shirt_info': i[4]
        }
        if all(value for value in waiting.values()):
            waiting_list.append(waiting)
        else:
            # Удаление пустой заявки из базы данных
            cursor.execute("DELETE FROM wait WHERE id = ?", (i[0],))
            conn.commit()

    # Закрытие соединения с базой данных
    conn.close()
    return render_template('admin.html', applications=applications_list, waiting=waiting_list)


@app.route('/go_code')
def open_codeditor():
    return render_template('codeeditor.html')


@app.route('/self')
def openself():
    return render_template('self.html')


@app.route('/runcode', methods=['POST'])
def run_code():
    try:
        data = request.get_json()
        code = data['code']
        
        # Capturing the standard output
        stdout = io.StringIO()
        sys.stdout = stdout

        # Redirect input to the Python code
        sys.stdin = io.StringIO("User input goes here")

        exec(code, globals())

        # Get the result and restore the original stdout and stdin
        result = stdout.getvalue()
        sys.stdout = sys.__stdout__
        sys.stdin = sys.__stdin__

        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()})


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/upload')
def indexofupload():
    return render_template('upload.html', show_view_files_button=False)


@app.route('/upload2', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return "No file part"

        file = request.files['file']

        if file.filename == '':
            return "No selected file"

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        return render_template('upload.html', show_view_files_button=True)
    except Exception as e:
        return "Error: " + str(e)


@app.route('/lessons')
def open_lessons():
    return render_template('lessons.html')


@app.route('/files')
def list_files():
    files = [(f, f) for f in os.listdir(app.config['UPLOAD_FOLDER'])]
    return render_template('view_files.html', files=files)


@app.route('/file/<filename>')
def view_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, as_attachment=True)


@app.route('/task')
def open_task():
    return render_template('task.html')


@app.route('/new_teacher', methods=['GET', 'POST'])
def openpersona():
    if request.method == 'POST':
        db = 'new_teachers.sqlite'
        mail = request.form.get('mail')
        password = request.form.get('password')
        teacher_name = request.form.get('teacher_name')
        phone_number = request.form.get('phone_number')
        shirt_info = request.form.get('shirt_info')
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO application (teacher_name, mail, phone_number, shirt_info) VALUES (?, ?, ?, ?)', (teacher_name, mail, phone_number, shirt_info))
        conn.commit()  # добавьте эту строку для сохранения изменений в базе данных
        conn.close()
        return render_template('wait.html')
    return render_template('persona.html')


print('asdasdasd')

if __name__ == '__main__':
    app.run(debug=True, port=8000)