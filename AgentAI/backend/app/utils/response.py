from typing import Any, Dict

def criar_response_ok(data: Dict[str, Any]) -> Dict[str, Any]:
    
    return {
        "success": True,
        "data": data,
        "error": None
    }


def criar_response_error(message: str, type: str = "GENERIC_ERROR") -> Dict[str, Any]:
    """
    Resposta padrão em caso de erro.
    """
    return {
        "success": False,
        "data": None,
        "error": {
            "type": type,
            "message": message
        }
    }


def ok_response(data: Dict[str, Any]) -> Dict[str, Any]:
    return criar_response_ok(data)


def error_response(message: str, type: str = "GENERIC_ERROR") -> Dict[str, Any]:
    """Alias para criar_response_error"""
    return criar_response_error(message, type)