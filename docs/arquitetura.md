# Arquitetura e Modelagem de Dados

O banco de dados será o **PostgreSQL**, utilizando o **SQLAlchemy** como ORM no FastAPI.

## 🗄️ Tabelas do Banco de Dados

### 1. `empresas` (Emitente da Nota)
Responsável por guardar as credenciais fiscais e o certificado.
- `id` (PK)
- `cnpj` (String 14)
- `razao_social` (String)
- `inscricao_estadual` (String)
- `certificado_path` (String)
- `certificado_senha` (String)
- `ambiente` (Integer - 1:Prod, 2:Homol)
- `csc_token` (String)
- `csc_id` (String)
- `chave_pix` (String) - Chave para recebimentos
- `pix_tipo` (Enum - CPF, CNPJ, EMAIL, CELULAR, ALEATORIA)
- `configurado` (Boolean)

### 2. `produtos` (Cardápio)
Cadastro de bebidas e refeições com dados fiscais básicos.
- `id` (PK)
- `descricao` (String)
- `preco_venda` (Numeric 10,2)
- `unidade` (String - UN, KG, LT)
- `categoria` (Enum - BEBIDA, REFEICAO, OUTROS)
- `imagem_url` (String) - URL ou path da foto do produto
- **Campos Fiscais:**
  - `ncm` (String 8) - Código NCM obrigatório
  - `cest` (String 7) - Código CEST (se houver Subst. Tributária)
  - `cfop` (String 4) - Ex: 5102 (Venda normal) ou 5405 (Subst. Trib)

### 3. `vendas` (Cabeçalho do Pedido)
Registro de cada venda realizada no restaurante.
- `id` (PK)
- `data_hora` (DateTime)
- `total_venda` (Numeric 10,2)
- `forma_pagamento` (String - 01:Dinheiro, 02:Cheque, 03:Cartao Cred, 04:Cartao Deb, 17:Pix)
- `status` (Enum - ABERTA, FINALIZADA, CANCELADA)
- `numero_mesa` (Integer) - Identificador da comanda

### 4. `venda_itens` (Detalhe do Pedido)
Itens consumidos em cada venda.
- `id` (PK)
- `venda_id` (FK -> vendas.id)
- `produto_id` (FK -> produtos.id)
- `quantidade` (Numeric 10,3)
- `preco_unitario` (Numeric 10,2)
- `valor_total` (Numeric 10,2)

### 5. `notas_fiscais` (Controle SEFAZ)
Registro do status de transmissão da nota fiscal.
- `id` (PK)
- `venda_id` (FK -> vendas.id)
- `chave_acesso` (String 44) - Gerada pela SEFAZ
- `status_sefaz` (String - PENDENTE, AUTORIZADA, ERRO, CANCELADA)
- `xml_autorizado` (Text) - Conteúdo do XML de retorno
- `protocolo` (String)
- `mensagem_erro` (Text) - Caso a SEFAZ rejeite a nota

## 🔄 Fluxo de Emissão Fiscal (NFC-e)
1. **Fechamento de Venda:** O PDV finaliza o pedido.
2. **Geração de XML:** O sistema lê os dados da venda + dados da empresa e gera o XML via `erpbrasil.nfe`.
3. **Assinatura:** O sistema usa o certificado `.pfx` para assinar digitalmente o XML.
4. **Transmissão:** Envia para o Webservice da SEFAZ.
5. **Retorno:** Se autorizado, o XML é guardado e o QR Code é gerado para impressão.

### 6. `usuarios` (Identidade e Acesso)
- `id` (PK)
- `username` (String) - Único
- `email` (String) - Único (Para login e recuperação)
- `hashed_password` (String)
- `full_name` (String)
- `created_at` (DateTime)

### 📊 Requisitos de Analíticos (Dashboard)
- As consultas de dashboard devem utilizar agregação SQL (`SUM`, `COUNT`, `GROUP BY`) para evitar transferência desnecessária de dados.
- Cache sugerido para dados de dashboard: 5-10 minutos (opcional para fase inicial).

### 7. `impressoras` (Hardware)
- `id` (PK)
- `nome` (String) - Ex: "Cozinha Central", "Bar Bebidas"
- `tipo` (Enum - TERMICA_80, TERMICA_58)
- `conexao` (Enum - USB, IP, BLUETOOTH)
- `endereco_ip` (String) - Se tipo IP
- `localizacao` (Enum - COZINHA, BAR, CAIXA)
- `ativa` (Boolean)
