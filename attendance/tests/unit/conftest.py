import sys
from unittest.mock import MagicMock, patch, mock_open

# ── Flask fake ────────────────────────────────────────────────
# Flask ka mock banana zaroori hai — attendance_api import karta hai
flask_mock = MagicMock()
flask_mock.Flask = MagicMock(return_value=MagicMock())
flask_mock.jsonify = MagicMock(return_value=MagicMock())
flask_mock.request  = MagicMock()
sys.modules['flask'] = flask_mock

# ── elasticapm fake ───────────────────────────────────────────
sys.modules['elasticapm']                    = MagicMock()
sys.modules['elasticapm.contrib']            = MagicMock()
sys.modules['elasticapm.contrib.flask']      = MagicMock()
sys.modules['elasticapm.handlers']           = MagicMock()
sys.modules['elasticapm.handlers.logging']   = MagicMock()

# ── mysql fake ────────────────────────────────────────────────
sys.modules['mysql']                         = MagicMock()
sys.modules['mysql.connector']               = MagicMock()

# ── yaml fake ─────────────────────────────────────────────────
yaml_mock = MagicMock()
yaml_mock.load = MagicMock(return_value={
    'mysql': {
        'host'    : 'localhost',
        'username': 'test_user',
        'password': 'test_pass',
        'db_name' : 'test_db'
    },
    'attendance': {
        'api_port': '8081'
    }
})
sys.modules['yaml'] = yaml_mock

# ── config mock ───────────────────────────────────────────────
MOCK_CONFIG = {
    'mysql': {
        'host'    : 'localhost',
        'username': 'test_user',
        'password': 'test_pass',
        'db_name' : 'test_db'
    },
    'attendance': {
        'api_port': '8081'
    }
}

# ── Import attendance_api with all mocks in place ─────────────
with patch('builtins.open', mock_open(read_data='dummy')), \
     patch('yaml.load', return_value=MOCK_CONFIG):
    import attendance_api