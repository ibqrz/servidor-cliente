"""Módulo comum ao servidor e ao cliente.

Protocolo (texto, uma mensagem por linha, UTF-8):
    Cliente -> Servidor : NICK <apelido>
    Servidor -> Cliente : OK <apelido_do_servidor>   (aceito)
                          ERRO <motivo>              (rejeitado; conexão fechada)
    Depois de aceito, ambos trocam linhas livremente, de forma assíncrona.
    A linha "FIM" encerra a sessão.
"""
import re
import socket
import threading

NICK_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
MAX_LINHA = 1024


class InputThread(threading.Thread):
    """Recebe linhas do socket e as exibe."""

    def __init__(self, leitor, nome_remoto: str, parar: threading.Event):
        super().__init__(daemon=True)
        self.leitor = leitor         
        self.nome_remoto = nome_remoto
        self.parar = parar

    def run(self):
        try:
            for linha in self.leitor:
                msg = linha.strip()
                if msg == "FIM":
                    print(f"\n[{self.nome_remoto} encerrou a conversa]")
                    break
                if msg:
                    print(f"\nIN  [{self.nome_remoto}] > {msg}")
        except (OSError, ValueError):
            pass 
        finally:
            self.parar.set()


class OutputThread(threading.Thread):
    """Lê do teclado e envia ao socket."""

    def __init__(self, dispositivo: socket.socket, parar: threading.Event):
        super().__init__(daemon=True)
        self.dispositivo = dispositivo
        self.parar = parar

    def run(self):
        try:
            while not self.parar.is_set():
                msg = input()
                if self.parar.is_set():   
                    break
                if not msg.strip():
                    continue
                self.dispositivo.sendall(f"{msg}\n".encode("utf-8"))
                print(f"OUT > {msg}")
                if msg == "FIM":
                    break
        except (EOFError, OSError) as e:
            if not self.parar.is_set():
                print(f"Erro no envio: {e}")
        finally:
            self.parar.set()


def executar_sessao(sock: socket.socket, leitor, nome_remoto: str):
    """Roda a conversa assíncrona até um dos lados encerrar."""
    parar = threading.Event()
    entrada = InputThread(leitor, nome_remoto, parar)
    saida = OutputThread(sock, parar)
    entrada.start()
    saida.start()

    parar.wait()                      
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    sock.close()
    entrada.join(timeout=2)

    if saida.is_alive():             
        print("[Sessão encerrada. Pressione ENTER para continuar]")
        saida.join()