from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import re
import uuid

app = Flask(__name__)
CORS(app) # Разрешаем запросы с фронтенда


active_tokens = {}

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root', 
        password='', 
        database='autoservice_db',
        cursorclass=pymysql.cursors.DictCursor
    )

def check_auth(req):
    token = req.headers.get('Authorization')
    if token and token in active_tokens:
        return active_tokens[token]
    return None

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # Валидация
    assert data is not None
    if not re.match(r'^[a-zA-Z0-9]{6,}$', data.get('login', '')):
        return jsonify({'error': 'Логин должен содержать только латиницу и цифры, не менее 6 символов'}), 400
    if len(data.get('password', '')) < 8:
        return jsonify({'error': 'Пароль должен быть не менее 8 символов'}), 400
    assert data is not None
    if not re.match(r'^[А-Яа-яЁё\s]+$', data.get('full_name', '')):
        return jsonify({'error': 'ФИО должно содержать только кириллицу и пробелы'}), 400
    assert data is not None
    if not re.match(r'^8\(\d{3}\)\d{3}-\d{2}-\d{2}$', data.get('phone', '')):
        return jsonify({'error': 'Телефон должен быть в формате 8(XXX)XXX-XX-XX'}), 400
    assert data is not None
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.get('email', '')):
        return jsonify({'error': 'Неверный формат email'}), 400

    hashed_pw = generate_password_hash(data['password']) # type: ignore
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO users (login, password_hash, full_name, phone, email, role_id) VALUES (%s, %s, %s, %s, %s, 2)"
            cursor.execute(sql, (data['login'], hashed_pw, data['full_name'], data['phone'], data['email']))
        conn.commit()
        return jsonify({'message': 'Регистрация успешна'}), 201
    except pymysql.err.IntegrityError:
        return jsonify({'error': 'Логин или email уже заняты'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            assert data is not None
            cursor.execute("SELECT * FROM users WHERE login = %s", (data.get('login'),))
            user = cursor.fetchone()
            
            assert data is not None
            if user and check_password_hash(user['password_hash'], data.get('password', '')):
                token = str(uuid.uuid4())
                active_tokens[token] = {'user_id': user['id'], 'role_id': user['role_id']}
                return jsonify({'token': token, 'role_id': user['role_id']}), 200
            else:
                return jsonify({'error': 'Неверный логин или пароль'}), 401
    finally:
        conn.close()

@app.route('/api/applications/my', methods=['GET'])
def get_my_applications():
    user = check_auth(request)
    if not user: return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT a.id, a.service_type, a.car_model, a.vin, a.start_date, p.name as payment_method, s.name as status
                FROM applications a
                JOIN payment_methods p ON a.payment_method_id = p.id
                JOIN application_statuses s ON a.status_id = s.id
                WHERE a.user_id = %s
                ORDER BY a.id DESC
            """
            cursor.execute(sql, (user['user_id'],))
            return jsonify(cursor.fetchall()), 200
    finally:
        conn.close()

@app.route('/api/applications', methods=['POST'])
def create_application():
    user = check_auth(request)
    if not user: return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO applications (user_id, service_type, car_model, vin, start_date, payment_method_id, status_id)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql, (user['user_id'], data['service_type'], data['car_model'], data['vin'], data['start_date'], data['payment_method_id'])) # type: ignore
        conn.commit()
        return jsonify({'message': 'Заявка создана'}), 201
    except pymysql.err.IntegrityError as e:
        # Обработка уникального ограничения по варианту 5
        if 'Duplicate entry' in str(e):
            return jsonify({'error': 'Заявка на этот VIN и дату уже существует!'}), 400
        return jsonify({'error': 'Ошибка базы данных'}), 500
    finally:
        conn.close()

@app.route('/api/admin/applications', methods=['GET'])
def get_all_applications():
    user = check_auth(request)
    if not user or user['role_id'] != 3: return jsonify({'error': 'Доступ запрещен'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT a.id, u.full_name, a.service_type, a.car_model, a.vin, a.start_date, s.name as status, a.status_id
                FROM applications a
                JOIN users u ON a.user_id = u.id
                JOIN application_statuses s ON a.status_id = s.id
                ORDER BY a.id DESC
            """
            cursor.execute(sql)
            return jsonify(cursor.fetchall()), 200
    finally:
        conn.close()

@app.route('/api/admin/applications/<int:app_id>/status', methods=['PATCH'])
def update_status(app_id):
    user = check_auth(request)
    if not user or user['role_id'] != 3: return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE applications SET status_id = %s WHERE id = %s", (data['status_id'], app_id)) # type: ignore
        conn.commit()
        return jsonify({'message': 'Статус обновлен'}), 200
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)