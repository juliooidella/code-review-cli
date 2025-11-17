"""
Utilitários compartilhados para geração do script PowerShell.
"""

from __future__ import annotations

from typing import Literal

Status = Literal["info", "success", "error"]


def sanitize_branch_name(branch: str) -> str:
    """
    Converte nomes de branch em strings seguras para nomes de arquivos.
    Substitui caracteres problemáticos por hífens e remove espaços repetidos.
    """
    safe = branch.strip()
    for token in ("/", "\\", ":", " ", ".", "~", "^", "[", "]"):
        safe = safe.replace(token, "-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe or "branch"


def ensure_utf8_bom(content: str, newline: str = "\r\n") -> bytes:
    """
    Normaliza as quebras de linha para CRLF e retorna bytes codificados em
    UTF-8 com BOM (utf-8-sig), garantindo compatibilidade com PowerShell 5.1.
    """
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\n", newline)
    return normalized.encode("utf-8-sig")


def format_ascii_log(message: str, status: Status = "info") -> str:
    """
    Retorna mensagem com prefixo ASCII padronizado para ser usado nos logs
    do PowerShell (evita emojis e caracteres problemáticos).
    """
    prefix_map = {
        "info": "[INFO]",
        "success": "[OK]",
        "error": "[ERR]",
    }
    prefix = prefix_map.get(status, "[INFO]")
    return f"{prefix} {message}"
