import logging

def get_logger():
    logger = logging.getLogger("demobot.v2")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def log_request(method, path, session_id, correlation_id, status_code, elapsed_ms):
    logger = get_logger()
    log_line = (
        f"method={method} path={path} session_id={session_id} correlation_id={correlation_id} "
        f"status_code={status_code} elapsed_ms={elapsed_ms:.2f}"
    )
    logger.info(log_line)
