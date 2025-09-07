import pytest
import os
import sqlite3
from unittest.mock import patch, MagicMock
from flask import Flask
from flask.testing import FlaskClient
from admin import admin_bp, get_db_connection, log_admin_action
from app import app

@pytest.fixture
def client() -> FlaskClient:
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def init_database():
    conn = sqlite3.connect('bfgminer_test.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE admin_users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, is_active BOOLEAN)''')
    cursor.execute('''CREATE TABLE admin_sessions (id INTEGER PRIMARY KEY, session_token TEXT, admin_id INTEGER)''')
    cursor.execute('''CREATE TABLE notifications (id INTEGER PRIMARY KEY, type TEXT, user_id INTEGER, message TEXT, is_read BOOLEAN)''')
    cursor.execute('''CREATE TABLE admin_audit_logs (id INTEGER PRIMARY KEY, admin_id INTEGER, action TEXT, details TEXT)''')
    cursor.execute("INSERT INTO admin_users (id, username, password_hash, is_active) VALUES (1, 'admin', '$2b$12$8N68I/eBxeG3AwxKahxusuuS7rGQO3KprmsC.OLp59fkPbyG7JsQm', 1)")
    conn.commit()
    yield conn
    conn.close()
    os.remove('bfgminer_test.db')

def test_get_db_connection(init_database):
    conn = get_db_connection()
    assert conn is not None
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table";')
    tables = [row[0] for row in cursor.fetchall()]
    assert 'admin_users' in tables
    conn.close()

def test_log_admin_action(init_database):
    log_admin_action(1, 'test_action', details='Test log entry')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_audit_logs WHERE action = ?', ('test_action',))
    log = cursor.fetchone()
    assert log is not None
    assert log[2] == 'test_action'
    conn.close()

@patch('admin.requests')
def test_validate_wallet_balance_success(mock_requests, client, init_database):
    mock_requests.post.return_value.json.return_value = {'result': hex(1000000000000000000)}
    mock_requests.get.return_value.json.return_value = {'ethereum': {'usd': 2500}}
    
    response = client.post('/admin/login', json={'username': 'admin', 'password': 'Admin123!'},
                          headers={'Content-Type': 'application/json'})
    assert response.status_code == 200
    
    response = client.post('/admin/api/wallets/validate-balance',
                          json={'wallet_address': '0x1234567890123456789012345678901234567890'},
                          headers={'Authorization': f'Bearer {response.json["sessionToken"]}'})
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert data['balance_eth'] == 1.0
    assert data['balance_usd'] == 2500.0

@patch('admin.requests')
def test_validate_wallet_balance_error(mock_requests, client, init_database):
    mock_requests.post.return_value.status_code = 500
    
    response = client.post('/admin/login', json={'username': 'admin', 'password': 'Admin123!'},
                          headers={'Content-Type': 'application/json'})
    assert response.status_code == 200
    
    response = client.post('/admin/api/wallets/validate-balance',
                          json={'wallet_address': '0x1234567890123456789012345678901234567890'},
                          headers={'Authorization': f'Bearer {response.json["sessionToken"]}'})
    assert response.status_code == 500
    data = response.json
    assert data['success'] is False


def test_admin_login_success(client, init_database):
    response = client.post('/admin/login',
                          json={'username': 'admin', 'password': 'Admin123!'},
                          headers={'Content-Type': 'application/json'})
    assert response.status_code == 200
    data = response.json
    assert data['success'] is True
    assert 'sessionToken' in data
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_sessions WHERE session_token = ?', (data['sessionToken'],))
    session = cursor.fetchone()
    assert session is not None
    conn.close()


def test_admin_login_failure(client, init_database):
    response = client.post('/admin/login',
                          json={'username': 'admin', 'password': 'wrong_password'},
                          headers={'Content-Type': 'application/json'})
    assert response.status_code == 401
    data = response.json
    assert data['success'] is False
    assert data['error'] == 'Invalid credentials'

@patch('admin.bcrypt.checkpw')
def test_admin_login_bcrypt_failure(mock_checkpw, client, init_database):
    mock_checkpw.return_value = False
    response = client.post('/admin/login',
                          json={'username': 'admin', 'password': 'Admin123!'},
                          headers={'Content-Type': 'application/json'})
    assert response.status_code == 401
    data = response.json
    assert data['success'] is False
    assert data['error'] == 'Invalid credentials'


def test_protected_route_unauthorized(client):
    response = client.get('/admin/dashboard')
    assert response.status_code == 401
    assert b'Admin authentication required' in response.data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
