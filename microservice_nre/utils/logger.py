"""Configuração centralizada do logger da aplicação.

Cria um logger nomeado pelo módulo com nível, formato e handlers definidos
pelas variáveis de ambiente via ``Settings``. Um ``execution_id`` UUID único
por processo é embutido em todas as mensagens, permitindo correlacionar logs
de uma mesma instância da aplicação mesmo em ambientes com múltiplos containers.

Handlers disponíveis (ativados via settings):
    - Console (``CONSOLE_LOG=true``): escreve em ``stdout``.
    - Arquivo (``LOG_FILE=<path>``): escreve em arquivo com encoding UTF-8.
"""

import logging
import sys
import time

from microservice_nre.utils.context import REQUEST_ID
from microservice_nre.utils.settings import settings


def default_formatter() -> logging.Formatter:
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] [%(short_name)s] request_id[%(request_id)s]: %(message)s ',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    formatter.converter = time.gmtime
    return formatter


class AppFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name.startswith(settings.PROJECT_NAME):
            name_parts = record.name.split('.')
            record.short_name = '.'.join(name_parts[-2:])
            record.request_id = REQUEST_ID.get()
            return True

        if record.levelno >= logging.WARNING:
            record.short_name = record.name
            record.request_id = 'external'
            return True

        return False


class CustomStreamHandler(logging.StreamHandler):
    def __init__(self) -> None:
        super().__init__(sys.stdout)


class CustomFileHandler(logging.FileHandler):
    def __init__(self, filename: str = settings.LOG_FILE) -> None:
        super().__init__(filename, mode='a', encoding='utf-8')


class CustomLogger(logging.Logger):
    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.setLevel(settings.LOG_LEVEL)
        self.propagate = False

        self.addHandler(CustomFileHandler())
        self.addHandler(CustomStreamHandler())
        self.addFilter(AppFilter())

        self.set_custom_formatter(default_formatter())

    def set_custom_formatter(self, formatter: logging.Formatter) -> None:
        for h in self.handlers:
            h.setFormatter(formatter)
