
from flask import Flask

app = Flask(__name__)


@app.route("/")
def pagina_inicial():
    return """
    <h1>Mercado Boa Compra</h1>
    <h2>Sistema de Controle de Estoque</h2>
    <p>O sistema está funcionando!</p>
    """


if __name__ == "__main__":
    app.run(debug=True)
