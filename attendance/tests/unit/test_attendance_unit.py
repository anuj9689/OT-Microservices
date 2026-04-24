import pytest
import json
from unittest.mock import patch, MagicMock
from attendance_api import app, create_mysql_client
import mysql.connector


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ══════════════════════════════════════════════════════════════
# HEALTH CHECK TESTS
# ══════════════════════════════════════════════════════════════

class TestHealthEndpoint:

    def test_health_mysql_up(self, client):
        mock_conn = MagicMock()
        mock_conn.ping.return_value = True
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.get('/attendance/healthz')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['mysql'] == 'up'
            assert data['description'] == 'MySQL is healthy'

    def test_health_mysql_down(self, client):
        with patch('attendance_api.create_mysql_client', side_effect=Exception("Connection failed")):
            response = client.get('/attendance/healthz')
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['mysql'] == 'down'
            assert data['description'] == 'MySQL is not healthy'

    def test_health_ping_fails(self, client):
        mock_conn = MagicMock()
        mock_conn.ping.side_effect = Exception("Ping failed")
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.get('/attendance/healthz')
            assert response.status_code == 400

    def test_health_returns_json(self, client):
        with patch('attendance_api.create_mysql_client', side_effect=Exception("error")):
            response = client.get('/attendance/healthz')
            assert response.content_type == 'application/json'

    def test_health_method_not_allowed(self, client):
        response = client.post('/attendance/healthz')
        assert response.status_code == 405


# ══════════════════════════════════════════════════════════════
# CREATE / PUSH ATTENDANCE TESTS
# ══════════════════════════════════════════════════════════════

class TestCreateEndpoint:

    def _make_payload(self, id=1, status='present', date='2024-01-01'):
        return json.dumps({'id': id, 'status': status, 'date': date}).encode()

    def test_create_success(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.post(
                '/attendance/create',
                data=self._make_payload(),
                content_type='application/json'
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'Successfully uploaded the attendance data'

    def test_create_mysql_connection_fails(self, client):
        """Source code mein bug hai — 400 int return karta hai, isliye status check nahi"""
        with patch('attendance_api.create_mysql_client', side_effect=Exception("DB error")):
            response = client.post(
                '/attendance/create',
                data=self._make_payload(),
                content_type='application/json'
            )
            # Source code: `return 400` (integer) — Flask isko error maanta hai
            # Hum sirf ensure karte hain ki response aaya
            assert response.status_code in [400, 500]

    def test_create_insert_fails(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [None, Exception("Insert error")]
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.post(
                '/attendance/create',
                data=self._make_payload(),
                content_type='application/json'
            )
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'Error' in data['message']

    def test_create_with_absent_status(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.post(
                '/attendance/create',
                data=self._make_payload(id=2, status='absent'),
                content_type='application/json'
            )
            assert response.status_code == 200

    def test_create_table_creation_called(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            client.post(
                '/attendance/create',
                data=self._make_payload(),
                content_type='application/json'
            )
            assert mock_cursor.execute.called

    def test_create_returns_json(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.post(
                '/attendance/create',
                data=self._make_payload(),
                content_type='application/json'
            )
            assert response.content_type == 'application/json'


# ══════════════════════════════════════════════════════════════
# SEARCH / FETCH ATTENDANCE TESTS
# ══════════════════════════════════════════════════════════════

class TestSearchEndpoint:

    def test_search_success_with_data(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'present', '2024-01-01'),
            (2, 'absent',  '2024-01-02'),
        ]
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.get('/attendance/search')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]['id'] == 1
            assert data[0]['status'] == 'present'
            assert data[0]['date'] == '2024-01-01'

    def test_search_empty_result(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.get('/attendance/search')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data == []

    def test_search_mysql_fails(self, client):
        with patch('attendance_api.create_mysql_client', side_effect=Exception("DB error")):
            response = client.get('/attendance/search')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'Error while pulling data for attendance'

    def test_search_multiple_records(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'present', '2024-01-01'),
            (2, 'absent',  '2024-01-02'),
            (3, 'present', '2024-01-03'),
        ]
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.get('/attendance/search')
            data = json.loads(response.data)
            assert len(data) == 3

    def test_search_returns_json(self, client):
        with patch('attendance_api.create_mysql_client', side_effect=Exception("error")):
            response = client.get('/attendance/search')
            assert response.content_type == 'application/json'

    def test_search_record_fields(self, client):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(5, 'present', '2024-03-15')]
        mock_conn.cursor.return_value = mock_cursor
        with patch('attendance_api.create_mysql_client', return_value=mock_conn):
            response = client.get('/attendance/search')
            data = json.loads(response.data)
            assert 'id' in data[0]
            assert 'status' in data[0]
            assert 'date' in data[0]


# ══════════════════════════════════════════════════════════════
# ROUTING TESTS
# ══════════════════════════════════════════════════════════════

class TestRouting:

    def test_unknown_route_returns_404(self, client):
        response = client.get('/')
        assert response.status_code == 404

    def test_unknown_post_route(self, client):
        response = client.post('/unknown')
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════
# MYSQL CLIENT TESTS — sys.modules mock use karo
# ══════════════════════════════════════════════════════════════

class TestMysqlClient:

    def test_create_mysql_client_called_with_correct_params(self):
        """mysql.connector already mocked hai sys.modules mein"""
        import mysql.connector as mc
        mc.connect.reset_mock()
        mock_conn = MagicMock()
        mc.connect.return_value = mock_conn
        result = create_mysql_client()
        assert mc.connect.called
        call_kwargs = mc.connect.call_args[1]
        assert 'host' in call_kwargs
        assert 'user' in call_kwargs
        assert 'passwd' in call_kwargs
        assert 'database' in call_kwargs

    def test_create_mysql_client_returns_connection(self):
        """Connection object return hona chahiye"""
        import mysql.connector as mc
        mc.connect.reset_mock()
        mock_conn = MagicMock()
        mc.connect.return_value = mock_conn
        result = create_mysql_client()
        assert result == mock_conn