"""Bounded public demo behind the hosting provider's HTTPS proxy."""
import os
bind = '0.0.0.0:' + os.environ.get('PORT', '10000')
workers = 2
worker_class = 'sync'
timeout = 120
graceful_timeout = 15
backlog = 16
max_requests = 200
max_requests_jitter = 20
limit_request_line = 2048
limit_request_fields = 40
limit_request_field_size = 4096
accesslog = None
errorlog = '-'
control_socket_disable = True
