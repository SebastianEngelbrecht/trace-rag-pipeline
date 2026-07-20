import logging
import sys
from structlog import configure, processors, stdlib, dev
import structlog

def setup_logging(log_level: str = "INFO"):
    """
    Configure structured logging for the application using structlog.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    configure(
        processors=[
            stdlib.add_log_level,
            stdlib.add_logger_name,
            processors.TimeStamper(fmt="iso"),
            processors.dict_tracebacks,
            # If running in a terminal, emit colored output. If running as a service, emit JSON.
            # We'll use the developer console renderer for now for readability.
            dev.ConsoleRenderer() 
        ],
        context_class=dict,
        logger_factory=stdlib.LoggerFactory(),
        wrapper_class=stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    """Get a structured logger instance."""
    return structlog.get_logger(name)