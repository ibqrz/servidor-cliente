import socket
import sys

from chat import MAX_LINHA, executar_sessao

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORTA = 5000
TIMEOUT_HANDSHAKE = 10


def tentar_conectar(nick: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT_HANDSHAKE)
    try:
        sock.connect((HOST, PORTA))
        leitor = sock.makefile("r", encoding="utf-8", newline="\n")
        sock.sendall(f"NICK {nick}\n".encode("utf-8"))
        resposta = leitor.readline(MAX_LINHA).strip()
    except (socket.timeout, OSError) as e:
        sock.close()
        return None, None, f"falha na conexão: {e}"

    if resposta.startswith("OK"):
        sock.settimeout(None)
        nick_servidor = resposta[2:].strip() or "Servidor"
        return sock, leitor, nick_servidor

    sock.close()
    return None, None, resposta[5:].strip() if resposta.startswith("ERRO") else (resposta or "sem resposta")


def main():
    try:
        while True:
            nick = input("Seu nickname: ").strip()
            sock, leitor, info = tentar_conectar(nick)
            if sock:
                break
            print(f"Conexão rejeitada: {info}\n")
    except (KeyboardInterrupt, EOFError):
        print("\nSaindo.")
        return

    print(f"Conectado a '{info}'. Digite FIM para encerrar.")
    executar_sessao(sock, leitor, info)


if __name__ == "__main__":
    main()