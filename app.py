import os

from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for, flash, session

from database import conectar, criar_tabelas

app = Flask(__name__)

# Chave de sessão configurada por variável de ambiente.
app.secret_key = os.environ["SECRET_KEY"]


@app.route("/")
def pagina_inicial():
    return render_template("index.html")
    


@app.route("/produtos", methods=["GET", "POST"])
def cadastrar_produto():

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip()
        preco_texto = request.form.get("preco", "").strip()
        quantidade_texto = request.form.get("quantidade", "").strip()
        minimo_texto = request.form.get("estoque_minimo", "").strip()

        if not nome or not categoria:
            flash("Nome e categoria são obrigatórios.", "erro")
            return render_template("produtos.html")

        try:
            preco = Decimal(preco_texto)
            quantidade = int(quantidade_texto)
            estoque_minimo = int(minimo_texto)

            if not preco.is_finite() or preco < 0:
                raise ValueError

            if preco.as_tuple().exponent < -2:
                raise ValueError

            if quantidade < 0 or estoque_minimo < 0:
                raise ValueError

            if not quantidade_texto.isdecimal():
                raise ValueError

            if not minimo_texto.isdecimal():
                raise ValueError

        except (ValueError, InvalidOperation):
            flash(
                "Informe preço e quantidades válidos e não negativos.",
                "erro"
            )
            return render_template("produtos.html")

        # Salva o produto no banco de dados.
        with conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO produtos
                (nome, categoria, preco, quantidade_atual, estoque_minimo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    nome,
                    categoria,
                    float(preco),
                    quantidade,
                    estoque_minimo
                )
            )

        flash("Produto cadastrado com sucesso!", "sucesso")
        return redirect(url_for("cadastrar_produto"))

    return render_template("produtos.html")




@app.route("/estoque")
def consultar_estoque():
    with conectar() as conexao:
        produtos = conexao.execute("""
            SELECT
                id_produto,
                nome,
                categoria,
                preco,
                quantidade_atual,
                estoque_minimo
            FROM produtos
            ORDER BY nome
        """).fetchall()

    return render_template(
        "estoque.html",
        produtos=produtos
    )




@app.route("/movimentacao", methods=["GET", "POST"])
def registrar_movimentacao():

    with conectar() as conexao:
        produtos = conexao.execute("""
            SELECT id_produto, nome, quantidade_atual
            FROM produtos
            ORDER BY nome
        """).fetchall()

    if request.method == "POST":

        id_texto = request.form.get("id_produto", "")
        tipo = request.form.get("tipo", "")
        quantidade_texto = request.form.get("quantidade", "")

        # Validar os dados recebidos
        if (
            not id_texto.isdecimal()
            or tipo not in ("entrada", "saida")
            or not quantidade_texto.isdecimal()
        ):
            flash("Dados da movimentação inválidos.", "erro")
            return render_template(
                "movimentacao.html", produtos=produtos
            )

        id_produto = int(id_texto)
        quantidade = int(quantidade_texto)

        if quantidade <= 0:
            flash("A quantidade deve ser maior que zero.", "erro")
            return render_template(
                "movimentacao.html", produtos=produtos
            )

        with conectar() as conexao:

            # Inicia uma transação para manter os dados consistentes
            conexao.execute("BEGIN IMMEDIATE")

            produto = conexao.execute("""
                SELECT id_produto, quantidade_atual
                FROM produtos
                WHERE id_produto = ?
            """, (id_produto,)).fetchone()

            if produto is None:
                flash("Produto não encontrado.", "erro")
                return render_template(
                    "movimentacao.html", produtos=produtos
                )

            estoque_anterior = produto["quantidade_atual"]

            if tipo == "saida" and quantidade > estoque_anterior:
                flash("Estoque insuficiente para essa saída.", "erro")
                return render_template(
                    "movimentacao.html", produtos=produtos
                )

            if tipo == "entrada":
                estoque_novo = estoque_anterior + quantidade
            else:
                estoque_novo = estoque_anterior - quantidade

            # Atualizar o estoque
            conexao.execute("""
                UPDATE produtos
                SET quantidade_atual = ?
                WHERE id_produto = ?
            """, (estoque_novo, id_produto))

            # Registrar a movimentação no histórico
            conexao.execute("""
                INSERT INTO movimentacoes
                (id_produto, tipo, quantidade)
                VALUES (?, ?, ?)
            """, (id_produto, tipo, quantidade))

        
        # Guardar os dados da movimentação para a tela de resultado
        session["ultima_movimentacao"] = {
            "id_produto": id_produto,
            "tipo": tipo,
            "quantidade": quantidade,
            "estoque_anterior": estoque_anterior,
            "estoque_novo": estoque_novo
        }

        return redirect(url_for("resultado_movimentacao"))


    return render_template(
        "movimentacao.html",
        produtos=produtos
    )



@app.route("/resultado")
def resultado_movimentacao():

    dados = session.pop("ultima_movimentacao", None)

    if dados is None:
        flash("Nenhuma movimentação recente para exibir.", "erro")
        return redirect(url_for("consultar_estoque"))

    with conectar() as conexao:
        produto = conexao.execute("""
            SELECT nome, estoque_minimo
            FROM produtos
            WHERE id_produto = ?
        """, (dados["id_produto"],)).fetchone()

    if produto is None:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("consultar_estoque"))

    return render_template(
        "resultado.html",
        dados=dados,
        produto=produto
    )



if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)

