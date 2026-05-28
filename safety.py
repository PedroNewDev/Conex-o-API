import re
from typing import Tuple

_INJECTION = [
    r"ignore\s+(previous|all|prior|above)\s+instructions?",
    r"forget\s+(your|all|previous)\s+(instructions?|rules?|role|persona)",
    r"esqueça\s+(suas|as|todas\s+as)?\s*instruções",
    r"ignore\s+as\s+instruções",
    r"act\s+as\s+(if\s+you\s+(are|were)|a\b|an\b)",
    r"aja\s+como\s+(se\s+você\s+fosse|um|uma)",
    r"você\s+é\s+agora\s+(um|uma|o|a)",
    r"you\s+are\s+now\s+(a|an|the)\b",
    r"\bjailbreak\b",
    r"\bDAN\b",
    r"pretend\s+(you\s+are|to\s+be)",
    r"finja\s+(ser|que\s+você\s+é)",
    r"\bsystem\s*prompt\b",
    r"prompt\s+do\s+sistema",
    r"nova\s+instrução\s+do\s+sistema",
    r"roleplay\s+as\b",
    r"override\s+(your|all)\s+(instructions?|rules?)",
    r"disable\s+(your|all)\s+(safety|filter|restriction)",
    r"desative\s+(seus|os)\s+(filtros?|restrições?|regras?)",
    r"modo\s+sem\s+restrições",
    r"unrestricted\s+mode",
    r"developer\s+mode",
]

_MALICIOUS = [
    r"\brm\s+-rf\b",
    r"\bsudo\s+",
    r"\bchmod\s+[0-7]{3,4}\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__\s*\(",
    r"\bos\.system\s*\(",
    r"\bsubprocess\b",
    r"\bDROP\s+TABLE\b",
    r"\bDELETE\s+FROM\b",
    r"';\s*--",
    r"\bTRUNCATE\s+TABLE\b",
    r"<script[\s>]",
    r"\bjavascript\s*:",
    r"\bonerror\s*=",
    r"wget\s+https?://.*\|\s*(?:ba)?sh",
    r"curl\s+https?://.*\|\s*(?:ba)?sh",
    r"\bbase64\s*-d\b.*\|\s*(?:ba)?sh",
]

_INAPPROPRIATE = [
    r"\b(como\s+fazer|how\s+to\s+(make|build|create))\s+(uma?\s+)?(bomba|bomb|explosiv)",
    r"\b(sintetizar|synthesize|produzir|produce|fabricar|make)\s+(droga|drug|narcotic|meth|cocain|heroín)",
    r"\b(hackear|hack|invadir|breach|comprometer)\s+(um?\s+)?(sistema\s+real|conta\s+real|servidor\s+real)",
    r"\b(criar|create|make|gerar|generate|escrever|write)\s+(vírus|virus|malware|ransomware|trojan|worm|spyware|keylogger)\b",
    r"\b(conteúdo|content)\s+(sexual|porn|explicit)\s+(envolvendo|involving|with)\s+(menor|child|criança|teen)",
]

_MSG_MAX_LEN = 4000


def validar_mensagem(mensagem: str) -> Tuple[bool, str]:
    if len(mensagem.strip()) < 2:
        return False, "Mensagem muito curta."

    if len(mensagem) > _MSG_MAX_LEN:
        return False, f"Mensagem muito longa. Máximo {_MSG_MAX_LEN} caracteres."

    for pattern in _INJECTION:
        if re.search(pattern, mensagem, re.IGNORECASE):
            return False, (
                "Tentativa de manipulação do sistema detectada. "
                "Por favor, faça uma pergunta legítima."
            )

    for pattern in _MALICIOUS:
        if re.search(pattern, mensagem, re.IGNORECASE):
            return False, (
                "Conteúdo potencialmente malicioso detectado. "
                "Esta solicitação não pode ser processada."
            )

    for pattern in _INAPPROPRIATE:
        if re.search(pattern, mensagem, re.IGNORECASE):
            return False, (
                "Solicitação inadequada detectada. "
                "Só posso ajudar com conteúdo construtivo e legal."
            )

    return True, ""
