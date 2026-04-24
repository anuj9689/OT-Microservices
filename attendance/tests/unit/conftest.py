import sys
from unittest.mock import MagicMock, patch, mock_open

# ── Step 1: elasticapm mock ───────────────────────────────────
# Pehle mock karo — attendance_api import se pehle
sys.modules['elasticapm']                  = MagicMock()
sys.modules['elasticapm.contrib']          = MagicMock()
sys.modules['elasticapm.contrib.flask']    = MagicMock()
sys.modules['elasticapm.handlers']         = MagicMock()
sys.modules['elasticapm.handlers.logging'] = MagicMock()

# ── Step 2: mysql mock ────────────────────────────────────────
mysql_mock                   = MagicMock()
connector_mock               = MagicMock()
mysql_mock.connector         = connector_mock
sys.modules['mysql']         = mysql_mock
sys.modules['mysql.connector'] = connector_mock

# ── Step 3: yaml mock ─────────────────────────────────────────
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

yaml_mock             = MagicMock()
yaml_mock.load        = MagicMock(return_value=MOCK_CONFIG)
yaml_mock.FullLoader  = MagicMock()
sys.modules['yaml']   = yaml_mock

# ── Step 4: Import attendance_api with mocks ──────────────────
# config.yaml open hone se rokna + yaml.load mock karna
with patch('builtins.open', mock_open(read_data='dummy')), \
     patch('yaml.load', return_value=MOCK_CONFIG):
    import attendance_api

# ── Step 5: App config inject karo manually ───────────────────
# attendance_api.py mein read_config() se jo config aata hai
# wo manually set karo
attendance_api.app.config['MYSQL_HOST']     = 'localhost'
attendance_api.app.config['MYSQL_USERNAME'] = 'test_user'
attendance_api.app.config['MYSQL_PASSWORD'] = 'test_pass'
attendance_api.app.config['MYSQL_DATABASE'] = 'test_db'