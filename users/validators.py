import re


def validate_cpf(value: str) -> str:
    digits = re.sub(r'\D', '', value)
    if len(digits) != 11 or len(set(digits)) == 1:
        raise ValueError('CPF inválido.')

    def _digit(body: str, factor_start: int) -> int:
        total = sum(int(d) * f for d, f in zip(body, range(factor_start, factor_start - len(body), -1)))
        r = total % 11
        return 0 if r < 2 else 11 - r

    if _digit(digits[:9], 10) != int(digits[9]):
        raise ValueError('CPF inválido.')
    if _digit(digits[:10], 11) != int(digits[10]):
        raise ValueError('CPF inválido.')
    return digits


def validate_placa(value: str) -> str:
    v = value.strip().upper().replace('-', '')
    mercosul = re.compile(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$')
    antiga = re.compile(r'^[A-Z]{3}[0-9]{4}$')
    if not (mercosul.match(v) or antiga.match(v)):
        raise ValueError('Placa inválida (use formato Mercosul ou antigo).')
    return v
