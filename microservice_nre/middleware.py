"""Middleware HTTP da aplicação.

Intercepta todas as requisições para adicionar cabeçalhos de rastreabilidade,
facilitando correlação de logs e monitoramento de latência.
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.responses import Response

from microservice_nre.utils.context import REQUEST_ID

logger = logging.getLogger(__name__)


async def request_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Adiciona rastreabilidade e métricas de latência a cada requisição HTTP.

    Gera um UUID único por requisição e o armazena em ``request.state.request_id``,
    disponível para uso em logs durante o ciclo de vida da requisição.

    Cabeçalhos adicionados à resposta:
        - ``X-Request-ID``: UUID único da requisição para correlação de logs.
        - ``X-Process-Time-MS``: Tempo total de processamento em milissegundos.

    Args:
        request: Objeto da requisição FastAPI/Starlette.
        call_next: Função que passa a requisição para o próximo handler da cadeia.

    Returns:
        Response com os cabeçalhos de rastreabilidade adicionados.
    """
    request.state.request_id = str(uuid.uuid4())
    REQUEST_ID.set(request.state.request_id)

    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)

    response.headers['X-Request-ID'] = request.state.request_id
    response.headers['X-Process-Time-MS'] = str(duration_ms)

    logger.info(
        'request=%s %s status=%s duration_ms=%s',
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response
