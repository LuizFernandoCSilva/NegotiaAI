from datetime import datetime
from typing import Optional, Union


def _parse_date(value: Union[str, datetime, None]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value)
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.split('T')[0], fmt)
        except Exception:
            continue
    return None


def verificar_data_vencimento(data_vencimento: Union[str, datetime, None], payment_date: Union[str, datetime, None]) -> bool:
    """Retorna True se payment_date for menor ou igual a data_vencimento.

    Se algum valor for None ou não puder ser parseado, retorna False.
    """
    due = _parse_date(data_vencimento)
    pay = _parse_date(payment_date)

    if due is None or pay is None:
        return False

    return pay.date() <= due.date()