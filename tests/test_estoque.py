
import pytest

import database
from app import app


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    # Cria um banco temporário para cada teste.
    banco_teste = tmp_path / "teste_mercado.db"
    monkeypatch.setattr(database, "DATABASE", banco_teste)

    # O app importou conectar diretamente de database.
    # A função utiliza a configuração temporária acima.
    database.criar_tabelas()

    app.config.update(
        TESTING=True,
        SECRET_KEY="chave-exclusiva-para-testes"
    )

    with app.test_client() as cliente:
        yield cliente


def cadastrar_produto(cliente, quantidade=15, minimo=5):
    return cliente.post("/produtos", data={
        "nome": "Macarrão 500 g",
        "categoria": "Alimentos",
        "preco": "4.50",
        "quantidade": str(quantidade),
        "estoque_minimo": str(minimo)
    })


def consultar_quantidade():
    with database.conectar() as conexao:
        produto = conexao.execute(
            "SELECT quantidade_atual FROM produtos WHERE id_produto = 1"
        ).fetchone()
        return produto["quantidade_atual"]


def test_cadastro_produto(cliente):
    resposta = cadastrar_produto(cliente)

    assert resposta.status_code == 302
    assert consultar_quantidade() == 15


def test_entrada_estoque(cliente):
    cadastrar_produto(cliente)

    resposta = cliente.post("/movimentacao", data={
        "id_produto": "1",
        "tipo": "entrada",
        "quantidade": "10"
    })

    assert resposta.status_code == 302
    assert consultar_quantidade() == 25


def test_saida_estoque(cliente):
    cadastrar_produto(cliente)

    resposta = cliente.post("/movimentacao", data={
        "id_produto": "1",
        "tipo": "saida",
        "quantidade": "8"
    })

    assert resposta.status_code == 302
    assert consultar_quantidade() == 7


def test_bloqueio_estoque_insuficiente(cliente):
    cadastrar_produto(cliente)

    resposta = cliente.post("/movimentacao", data={
        "id_produto": "1",
        "tipo": "saida",
        "quantidade": "100"
    })

    assert resposta.status_code == 200
    assert consultar_quantidade() == 15

    with database.conectar() as conexao:
        total = conexao.execute(
            "SELECT COUNT(*) FROM movimentacoes"
        ).fetchone()[0]

    assert total == 0


def test_alerta_estoque_baixo(cliente):
    cadastrar_produto(cliente, quantidade=10, minimo=5)

    resposta = cliente.post("/movimentacao", data={
        "id_produto": "1",
        "tipo": "saida",
        "quantidade": "5"
    }, follow_redirects=True)

    assert resposta.status_code == 200
    assert consultar_quantidade() == 5
    assert "Estoque baixo".lower() in resposta.get_data(
        as_text=True
    ).lower()
