import logging
import uuid
from flask import has_request_context, request, g

CORRELATION_ID_HEADER = 'X-Correlation-ID'


class RequestCorrelationIdFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.correlation_id = getattr(g, 'correlation_id', 'N/A')
        else:
            record.correlation_id = 'no-request'
        return True


def init_logging():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] cid=[%(correlation_id)s] %(message)s'
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestCorrelationIdFilter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
