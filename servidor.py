import socket
import sys

from chat import MAX_LINHA, NICK_RE, executar_sessao

HOST = "0.0.0.0"
PORTA = 5000
TIMEOUT_HANDSHAKE = 10 


def validar_nick(nick: str, nick_servidor: str):
    if not NICK_RE.match(nick):
        return "nick inválido (3-16 caracteres: letras, números ou _)"
    if nick.lower() == nick_servidor.lower():
        return "nick já está em uso"
    return None


def negociar(conn: socket.socket, leitor, nick_servidor: str):
    conn.settimeout(TIMEOUT_HANDSHAKE)
    try:
        linha = leitor.readline(MAX_LINHA).strip()
    except (socket.timeout, OSError, UnicodeDecodeError):
        return None

    partes = linha.split(" ", 1)
    if len(partes) != 2 or partes[0] != "NICK":
        conn.sendall(b"ERRO esperado: NICK <apelido>\n")
        return None

    nick = partes[1].strip()
    motivo = validar_nick(nick, nick_servidor)
    if motivo:
        conn.sendall(f"ERRO {motivo}\n".encode("utf-8"))
        return None

    conn.sendall(f"OK {nick_servidor}\n".encode("utf-8"))
    conn.settimeout(None) 
    return nick


def main():
    nick_servidor = sys.argv[1] if len(sys.argv) > 1 else "Servidor"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORTA))
        srv.listen(1)
        print(f"Servidor '{nick_servidor}' aguardando em {HOST}:{PORTA} (Ctrl+C para sair)")

        try:
            while True:
                conn, addr = srv.accept()
                print(f"\nConexão de {addr[0]}:{addr[1]}")
                leitor = conn.makefile("r", encoding="utf-8", newline="\n")

                nick = negociar(conn, leitor, nick_servidor)
                if nick is None:
                    print("Conexão rejeitada. Aguardando próxima...")
                    try:
                        leitor.close()
                        conn.close()
                    except OSError:
                        pass
                    continue

                print(f"'{nick}' aceito. Conversa iniciada (digite FIM para encerrar).")
                executar_sessao(conn, leitor, nick)
                print("Aguardando próxima conexão...")
        except KeyboardInterrupt:
            print("\nServidor finalizado.")


if __name__ == "__main__":
    main()