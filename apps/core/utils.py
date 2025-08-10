import logging
import requests
from typing import List, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

def consultar_api_externa(url: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Función auxiliar reutilizable para consultar APIs externas.
    Maneja timeouts, rate limits, y otros errores de forma robusta.
    """
    try:
        response = requests.get(url, timeout=timeout)

        if response.status_code == 429:
            logger.warning("Límite de peticiones excedido. URL: %s", url)
            return []

        response.raise_for_status()
        return response.json().get('geonames', [])

    except requests.Timeout:
        logger.error("Timeout al conectar con API. URL: %s", url)
    except requests.RequestException as e:
        logger.error("Error de red: %s. URL: %s", e, url)

    return []
