# Conexão com API do Grok (xAI)

Projeto de validação de comunicação com a API do Grok (xAI) usando Python e Flask.

## Pré-requisitos

- Python 3.8+
- Chave de acesso da API xAI

## Como obter a chave de API

1. Acesse [console.x.ai](https://console.x.ai)
2. Faça login com sua conta X (Twitter)
3. Vá em **API Keys** e clique em **Create API Key**
4. Copie a chave gerada

## Configuração do ambiente

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar a chave de API

Copie o arquivo `.env.example` para `.env` e preencha a chave:

```
XAI_API_KEY=sua_chave_aqui
```

### 3. Executar o script de validação

```bash
python main.py
```

### 4. Executar a interface web (chat)

```bash
python app.py
```

Acesse `http://127.0.0.1:5000` no navegador.

## Exemplo de saída (main.py)

```
Conectando à API do Grok (xAI)...

=== Resposta da API ===
Modelo: grok-beta
Tokens utilizados: 92

Resposta:
Uma curiosidade interessante sobre inteligência artificial é que...
```
