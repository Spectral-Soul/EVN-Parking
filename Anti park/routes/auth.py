from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, execute_db, query_db

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = query_db('SELECT id FROM users WHERE username = ?', (username,), one=True)
    if user:
        return jsonify({'error': 'User already exists'}), 400

    hashed_pw = generate_password_hash(password)
    execute_db('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))

    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)

    if user and check_password_hash(user['password'], password):
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = user['is_admin']
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user['id'], 'username': user['username'], 'is_admin': user['is_admin']}
        })
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})
