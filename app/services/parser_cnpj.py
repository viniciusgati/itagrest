import re
import subprocess
import tempfile
import os
from typing import Optional
from pydantic import BaseModel


class DadosCartaoCNPJ(BaseModel):
    cnpj: str = ""
    razao_social: str = ""
    nome_fantasia: Optional[str] = ""
    logradouro: Optional[str] = ""
    numero: Optional[str] = ""
    complemento: Optional[str] = ""
    bairro: Optional[str] = ""
    municipio: Optional[str] = ""
    uf: Optional[str] = ""
    cep: Optional[str] = ""
    telefone: Optional[str] = ""
    email: Optional[str] = ""


ADDRESS_LABELS = {
    "LOGRADOURO", "NÚMERO", "NUMERO", "COMPLEMENTO",
    "CEP", "BAIRRO/DISTRITO", "BAIRRO", "MUNICÍPIO", "MUNICIPIO", "UF",
}
ESTADOS = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
    "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO",
}


def extrair_cnpj_do_pdf(pdf_content: bytes) -> DadosCartaoCNPJ:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_content)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["pdftotext", tmp_path, "-"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            raise ValueError("Falha ao extrair texto do PDF")
        texto = result.stdout
    finally:
        os.unlink(tmp_path)

    dados = DadosCartaoCNPJ()
    lines = [l.strip() for l in texto.split("\n")]

    # CNPJ
    cnpj_match = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
    if cnpj_match:
        dados.cnpj = cnpj_match.group()

    # Razão Social: linha após "NOME EMPRESARIAL"
    for i, line in enumerate(lines):
        if line == "NOME EMPRESARIAL":
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j] and not any(x in lines[j] for x in ("TÍTULO", "PORTE", "********")):
                    dados.razao_social = lines[j]
                    break

    # Nome Fantasia: linha após "NOME DE FANTASIA" (ignorar labels seguintes como PORTE)
    for i, line in enumerate(lines):
        if "NOME DE FANTASIA" in line:
            for j in range(i + 1, min(i + 6, len(lines))):
                candidate = lines[j]
                if candidate and candidate not in ("********", "PORTE", "ME", ""):
                    dados.nome_fantasia = candidate
                    break

    # Endereço: bloco entre "LOGRADOURO" e "ENDEREÇO ELETRÔNICO"
    # Layout: LABELS em grupo, depois VALUES em grupo na mesma ordem
    # Labels: LOGRADOURO, NÚMERO, COMPLEMENTO, CEP, BAIRRO/DISTRITO, MUNICÍPIO, UF
    # Values: <logradouro>, <numero>, <complemento>, <cep>, <bairro>, <municipio>, <uf>
    start_idx = -1
    for i, line in enumerate(lines):
        if line == "LOGRADOURO":
            start_idx = i
            break

    if start_idx >= 0:
        values = []
        for j in range(start_idx, len(lines)):
            line = lines[j]
            if line == "ENDEREÇO ELETRÔNICO":
                break
            if not line or line in ADDRESS_LABELS:
                continue
            if any(x in line for x in ("CÓDIGO", "SITUAÇÃO", "SITUACAO", "MOTIVO", "APROVADO")):
                break
            values.append(line)

        if len(values) >= 1:
            dados.logradouro = values[0]
        if len(values) >= 2:
            dados.numero = values[1]
        if len(values) >= 3:
            dados.complemento = values[2]
        if len(values) >= 4:
            dados.cep = values[3]
        if len(values) >= 5:
            dados.bairro = values[4]
        if len(values) >= 6:
            dados.municipio = values[5].title()
        if len(values) >= 7:
            uf_candidate = values[6].upper()
            if uf_candidate in ESTADOS:
                dados.uf = uf_candidate

    # Telefone
    phone_match = re.search(r"\(\d{2}\)\s?\d{4,5}-\d{4}", texto)
    if phone_match:
        dados.telefone = phone_match.group()

    # Email
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", texto)
    if email_match:
        dados.email = email_match.group().lower()

    return dados
