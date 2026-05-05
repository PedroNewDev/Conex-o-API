-- Banco de dados: aula
-- Projeto: Conex-o-API (Chat com Gemini)

CREATE TABLE IF NOT EXISTS conversas (
    id SERIAL PRIMARY KEY,
    sessao_id VARCHAR(100) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mensagens (
    id SERIAL PRIMARY KEY,
    conversa_id INTEGER NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    remetente VARCHAR(10) NOT NULL CHECK (remetente IN ('usuario', 'ia')),
    conteudo TEXT NOT NULL,
    modelo VARCHAR(50),
    tokens INTEGER,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
