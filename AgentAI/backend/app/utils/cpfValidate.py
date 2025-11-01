def validar_cpf(cpf: str) -> bool:
    cpf_limpo = ''.join(filter(str.isdigit, cpf or ""))
    
    if len(cpf_limpo) != 11:
        return False
    if cpf_limpo == cpf_limpo[0] * 11:
        return False
    
    soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[9]) != digito1:
        return False
    
    soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf_limpo[10]) == digito2


def normalizar_cpf(cpf: str) -> str:
    
    return ''.join(filter(str.isdigit, cpf or ""))
