import logging
import os
from datetime import datetime

# Criar diretório de logs se não existir
LOG_DIR = "storage/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configuração básica do logger
logger = logging.getLogger("itagrest")
logger.setLevel(logging.INFO)

# Formato do Log: [DATA] [LEVEL] MENSAGEM
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

# Handler para console (Para ver no terminal)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handler para arquivo (Log acumulado)
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "app.log"))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def log_venda(venda_id: int, total: float, forma_pagamento: str):
    """Log resumido de cada venda realizada."""
    logger.info(f"VENDA REALIZADA | ID: {venda_id} | TOTAL: R$ {total:.2f} | FORMA: {forma_pagamento}")

def log_sefaz_evento(venda_id: int, status: str, motivo: str, chave: str = ""):
    """Log de eventos de comunicação com a SEFAZ."""
    msg = f"SEFAZ EVENTO | VENDA: {venda_id} | STATUS: {status} | MOTIVO: {motivo}"
    if chave:
        msg += f" | CHAVE: {chave}"
    logger.info(msg)

def log_xml_auditoria(venda_id: int, xml_content: str):
    """Salva o XML completo em arquivo separado para auditoria técnica."""
    xml_path = os.path.join(LOG_DIR, f"xml_venda_{venda_id}.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    logger.info(f"XML AUDITORIA SALVO | VENDA: {venda_id} | PATH: {xml_path}")
