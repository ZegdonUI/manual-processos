"""Servidor do Manual de Processos.

Serve os arquivos da pasta e aceita upload/remoção de imagens de qualquer
pessoa que abrir o link. Imagens removidas ou trocadas não são apagadas:
vão para img/_lixeira/ (dá para recuperar).

Uso: python servidor.py [porta] [--rede] [--somente-leitura]
  --rede             escuta em todas as interfaces (para compartilhar na rede)
  --somente-leitura  só quem acessa pelo próprio PC (localhost) pode editar
"""
import json
import os
import re
import socket
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_IMG = os.path.join(RAIZ, "img")
MANIFESTO = os.path.join(PASTA_IMG, "manifesto.json")
LIMITE = 15 * 1024 * 1024  # 15 MB
SECAO_OK = re.compile(r"^[a-z0-9-]+/[a-z0-9-]+$")
GRUPOS = {"vistas", "usos", "exemplos"}


TEXTOS = os.path.join(RAIZ, "textos.json")                    # textos editados no site
HISTORICO = os.path.join(RAIZ, "textos-historico.jsonl")      # toda alteração de texto (antes/depois)
CAMPO_OK = re.compile(r"^[a-zA-Z]+(\.\d{1,2})?$")
LIMITE_TEXTO = 5000  # caracteres


def ler_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def salvar_json(caminho, m):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)


def ler_manifesto():
    return ler_json(MANIFESTO)


def salvar_manifesto(m):
    salvar_json(MANIFESTO, m)


SO_LOCAL = "--somente-leitura" in sys.argv
TRAVA = threading.Lock()  # várias pessoas editando ao mesmo tempo: um upload por vez no manifesto


def com_trava(fn):
    def envolto(self):
        with TRAVA:
            return fn(self)
    return envolto
LIXEIRA = os.path.join(PASTA_IMG, "_lixeira")


def apagar(secao, arquivo):
    """Não apaga de verdade: move para img/_lixeira/<processo>__<secao>__<arquivo>."""
    if arquivo and re.fullmatch(r"[a-z0-9-]+\.jpg", arquivo):
        os.makedirs(LIXEIRA, exist_ok=True)
        destino = os.path.join(LIXEIRA, secao.replace("/", "__") + "__" + arquivo)
        try:
            os.replace(os.path.join(PASTA_IMG, *secao.split("/"), arquivo), destino)
        except FileNotFoundError:
            pass


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=RAIZ, **kw)

    def end_headers(self):
        caminho = urlparse(self.path).path
        if caminho.startswith(("/img/manifesto.json", "/textos.json", "/api/")):
            self.send_header("Cache-Control", "no-store")
        elif caminho == "/" or caminho.endswith(".html"):
            self.send_header("Cache-Control", "no-cache")  # sempre pega a versão nova da página
        super().end_headers()

    # ---- helpers ----
    def local(self):
        """Pode editar? Todos, exceto quando iniciado com --somente-leitura (aí só localhost)."""
        return not SO_LOCAL or self.client_address[0] in ("127.0.0.1", "::1", "::ffff:127.0.0.1")

    def json(self, codigo, dados):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def params(self):
        q = parse_qs(urlparse(self.path).query)
        secao = q.get("secao", [""])[0]
        grupo = q.get("grupo", [""])[0]
        try:
            indice = int(q.get("indice", ["-1"])[0])
        except ValueError:
            indice = -1
        if not SECAO_OK.match(secao) or grupo not in GRUPOS:
            return None
        return secao, grupo, indice

    def conflito(self, lista, indice):
        """Quem troca/remove informa o arquivo que via; se outra pessoa já mexeu, recusa."""
        esperado = parse_qs(urlparse(self.path).query).get("arquivo", [""])[0] or None
        atual = lista[indice] if 0 <= indice < len(lista) else None
        return esperado != atual

    # ---- rotas ----
    def do_GET(self):
        if urlparse(self.path).path == "/api/status":
            return self.json(200, {"podeEditar": self.local()})
        return super().do_GET()

    @com_trava
    def do_POST(self):
        if urlparse(self.path).path != "/api/imagem":
            return self.json(404, {"erro": "rota inexistente"})
        if not self.local():
            return self.json(403, {"erro": "edição desativada (servidor em modo somente leitura)"})
        p = self.params()
        if not p:
            return self.json(400, {"erro": "parâmetros inválidos"})
        secao, grupo, indice = p
        tamanho = int(self.headers.get("Content-Length") or 0)
        if self.headers.get("Content-Type") != "image/jpeg" or not 0 < tamanho <= LIMITE:
            return self.json(400, {"erro": "envie JPEG de até 15 MB"})
        dados = self.rfile.read(tamanho)
        if not dados.startswith(b"\xff\xd8"):
            return self.json(400, {"erro": "arquivo não é JPEG"})

        m = ler_manifesto()
        lista = m.setdefault(secao, {}).setdefault(grupo, [])
        if indice >= 0 and self.conflito(lista, indice):
            return self.json(409, {"erro": "outra pessoa alterou esta imagem; a página foi atualizada, tente de novo", "manifesto": m})
        nome = f"{grupo[:-1]}-{int(time.time() * 1000)}.jpg"
        pasta = os.path.join(PASTA_IMG, *secao.split("/"))
        os.makedirs(pasta, exist_ok=True)
        with open(os.path.join(pasta, nome), "wb") as f:
            f.write(dados)

        if 0 <= indice < len(lista):          # troca
            apagar(secao, lista[indice])
            lista[indice] = nome
        elif grupo == "vistas" and 0 <= indice < 50:  # vista em posição fixa
            lista.extend([None] * (indice + 1 - len(lista)))
            lista[indice] = nome
        else:                                  # acrescenta na galeria
            lista.append(nome)
        salvar_manifesto(m)
        return self.json(200, m)

    @com_trava
    def do_PUT(self):
        """Salva um texto: PUT /api/texto?secao=<chave>&campo=<campo>, corpo = texto UTF-8."""
        if urlparse(self.path).path != "/api/texto":
            return self.json(404, {"erro": "rota inexistente"})
        if not self.local():
            return self.json(403, {"erro": "edição desativada (servidor em modo somente leitura)"})
        q = parse_qs(urlparse(self.path).query)
        secao = q.get("secao", [""])[0]
        campo = q.get("campo", [""])[0]
        if not SECAO_OK.match(secao) or not CAMPO_OK.match(campo):
            return self.json(400, {"erro": "parâmetros inválidos"})
        tamanho = int(self.headers.get("Content-Length") or 0)
        if not 0 <= tamanho <= LIMITE_TEXTO * 4:
            return self.json(400, {"erro": "texto muito longo"})
        try:
            texto = self.rfile.read(tamanho).decode("utf-8").strip()
        except UnicodeDecodeError:
            return self.json(400, {"erro": "texto inválido"})
        if len(texto) > LIMITE_TEXTO:
            return self.json(400, {"erro": "texto muito longo"})

        m = ler_json(TEXTOS)
        antes = m.get(secao, {}).get(campo)
        m.setdefault(secao, {})[campo] = texto
        salvar_json(TEXTOS, m)
        with open(HISTORICO, "a", encoding="utf-8") as f:
            f.write(json.dumps({"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "secao": secao, "campo": campo,
                                "antes": antes, "depois": texto}, ensure_ascii=False) + "\n")
        return self.json(200, m)

    @com_trava
    def do_DELETE(self):
        if urlparse(self.path).path != "/api/imagem":
            return self.json(404, {"erro": "rota inexistente"})
        if not self.local():
            return self.json(403, {"erro": "edição desativada (servidor em modo somente leitura)"})
        p = self.params()
        if not p:
            return self.json(400, {"erro": "parâmetros inválidos"})
        secao, grupo, indice = p
        m = ler_manifesto()
        lista = m.get(secao, {}).get(grupo, [])
        if not 0 <= indice < len(lista) or lista[indice] is None or self.conflito(lista, indice):
            return self.json(409, {"erro": "outra pessoa alterou esta imagem; a página foi atualizada, confira", "manifesto": m})
        apagar(secao, lista[indice])
        if grupo == "vistas":
            lista[indice] = None
        else:
            lista.pop(indice)
        salvar_manifesto(m)
        return self.json(200, m)


class Servidor(ThreadingHTTPServer):
    # Sem isto o Windows deixa dois servidores na mesma porta (um com código velho),
    # e cada pessoa cai num diferente.
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    porta = int(args[0]) if args else 8080
    host = "0.0.0.0" if "--rede" in sys.argv else "127.0.0.1"
    try:
        servidor = Servidor((host, porta), Handler)
    except OSError:
        print(f"\n  A porta {porta} já está em uso: o manual já está aberto em outra janela.")
        print("  Use essa janela ou feche-a antes de abrir de novo.\n")
        sys.exit(1)
    modo = "todos podem editar" if not SO_LOCAL else "edição só neste PC"
    print(f"  Servidor ativo em http://localhost:{porta}  ({modo})  — Ctrl+C para parar")
    servidor.serve_forever()
