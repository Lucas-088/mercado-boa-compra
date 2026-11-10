
import sqlite3
from pathlib import Path

# Pasta onde o banco de dados será armazenado
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "mercado.db"


def conectar():
    """Cria uma conexão com o banco SQLite."""
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row

    # Habilita o controle de chaves estrangeiras
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def criar_tabelas():
    """Cria as tabelas necessárias para o estoque."""

    with conectar() as conexao:

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT NOT NULL,
                preco NUMERIC NOT NULL CHECK (preco >= 0),
                quantidade_atual INTEGER NOT NULL
                    CHECK (quantidade_atual >= 0),
                estoque_minimo INTEGER NOT NULL
                    CHECK (estoque_minimo >= 0)
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
                id_produto INTEGER NOT NULL,
                tipo TEXT NOT NULL
                    CHECK (tipo IN ('entrada', 'saida')),
                quantidade INTEGER NOT NULL
                    CHECK (quantidade > 0),
                data_movimentacao TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (id_produto)
                    REFERENCES produtos(id_produto)
            )
        """)

    print("Banco de dados inicializado com sucesso!")


if __name__ == "__main__":
    criar_tabelas()
