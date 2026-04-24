import sys
from unittest.mock import MagicMock, patch, mock_open

# elasticapm fake
sys.modules['elasticapm'] = MagicMock()
sys.modules['elasticapm.contrib'] = MagicMock()
sys.modules['elasticapm.contrib.flask'] = MagicMock()
sys.modules['elasticapm.handlers'] = MagicMock()
sys.modules['elasticapm.handlers.logging'] = MagicMock()

# mysql fake
sys.modules['mysql'] = MagicMock()
sys.modules['mysql.connector'] = MagicMock()

# config mock
MOCK_CONFIG = {
    'mysql': {
        'host': 'localhost',
        'username': 'test_user',
        'password': 'test_pass',
        'db_name': 'test_db'
    }
}

with patch('builtins.open', mock_open(read_data='dummy')), \
     patch('yaml.load', return_value=MOCK_CONFIG):
    import attendance_api
