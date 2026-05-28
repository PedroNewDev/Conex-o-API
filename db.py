import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def conectar_banco():
    try:
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME", "aula"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            options="-c client_encoding=UTF8",
        )
    except UnicodeDecodeError as e:
        # libpq on Windows/Portuguese locale sends Latin-1 error messages
        msg = e.object.decode("cp1252", errors="replace")
        raise Exception(f"Erro de conexão PostgreSQL: {msg}") from None


def inicializar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.execute(f.read())
    conexao.commit()
    cursor.close()
    conexao.close()


def criar_conversa(sessao_id):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO conversas (sessao_id) VALUES (%s) RETURNING id",
        (sessao_id,)
    )
    conversa_id = cursor.fetchone()[0]
    conexao.commit()
    cursor.close()
    conexao.close()
    return conversa_id


def buscar_conversa_por_sessao(sessao_id):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id FROM conversas WHERE sessao_id = %s ORDER BY criado_em DESC LIMIT 1",
        (sessao_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conexao.close()
    return row[0] if row else None


def inserir_mensagem(conversa_id, remetente, conteudo, modelo=None, tokens=None):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO mensagens (conversa_id, remetente, conteudo, modelo, tokens) VALUES (%s, %s, %s, %s, %s)",
        (conversa_id, remetente, conteudo, modelo, tokens)
    )
    conexao.commit()
    cursor.close()
    conexao.close()


def ler_mensagens(conversa_id):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id, remetente, conteudo, modelo, tokens, criado_em FROM mensagens WHERE conversa_id = %s ORDER BY criado_em",
        (conversa_id,)
    )
    mensagens = []
    for row in cursor.fetchall():
        mensagens.append({
            "id": row[0],
            "remetente": row[1],
            "conteudo": row[2],
            "modelo": row[3],
            "tokens": row[4],
            "criado_em": str(row[5])
        })
    cursor.close()
    conexao.close()
    return mensagens
