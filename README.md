# Conexão com API do Gemini (Google)

Projeto de validação de comunicação com a API do Gemini usando Python e Flask.

## Como obter a chave de API (gratuita)

1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Faça login com sua conta Google
3. Clique em **Get API Key** → **Create API Key**
4. Copie a chave gerada

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Crie um arquivo `.env` com:
```
GEMINI_API_KEY=sua_chave_aqui
```

## Executar script de validação

```bash
python main.py
```

## Executar interface web (chat)

```bash
python app.py
```

Acesse `http://127.0.0.1:5000` no navegador.

## Exemplo de saída

```
Conectando à API do Gemini (Google)...

=== Resposta da API ===
Modelo: gemini-2.0-flash

Resposta:
Uma curiosidade interessante sobre inteligência artificial é que...
```
