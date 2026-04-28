# Conexão com API do ChatGPT (OpenAI)

Projeto de validação de comunicação com a API da OpenAI usando Python.

## Pré-requisitos

- Python 3.8+
- Chave de acesso da API OpenAI

## Como obter a chave de API

1. Acesse [platform.openai.com](https://platform.openai.com)
2. Crie uma conta ou faça login
3. Vá em **API Keys** e clique em **Create new secret key**
4. Copie a chave gerada

## Configuração do ambiente

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar a chave de API

Crie um arquivo `.env` na raiz do projeto (ou configure a variável de ambiente diretamente):

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sua_chave_aqui"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="sua_chave_aqui"
```

Ou copie o arquivo `.env.example` para `.env` e preencha a chave:
```
OPENAI_API_KEY=sua_chave_aqui
```

### 3. Executar o script

```bash
python main.py
```

## Exemplo de saída

```
Conectando à API do ChatGPT (OpenAI)...

=== Resposta da API ===
Modelo: gpt-3.5-turbo-0125
Tokens utilizados: 87

Resposta:
Uma curiosidade interessante sobre inteligência artificial é que...
```
