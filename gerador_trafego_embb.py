import time
import os
import sys

def iniciar_trafego_embb(host_cliente, ip_servidor, porta_servidor, largura_banda_mbps, duracao_segundos, log_dir):
    """
    Inicia um fluxo de tráfego eMBB usando iperf UDP.

    Args:
        host_cliente (mininet.node.Host): O objeto host Mininet que atuará como cliente.
        ip_servidor (str): O endereço IP do servidor iperf.
        porta_servidor (int): A porta TCP/UDP do servidor iperf.
        largura_banda_mbps (int): A largura de banda alvo em Mbps.
        duracao_segundos (int): A duração do teste em segundos.
        log_dir (str): Diretório para salvar os logs.
    """
    log_file_path = os.path.join(log_dir, "iperf_embb_log.txt")

    # Garante que o diretório de log exista
    os.makedirs(log_dir, exist_ok=True)

    print(f"[eMBB Gen] Iniciando iperf TCP de {host_cliente.name} para {ip_servidor}:{porta_servidor} "
          f"com {largura_banda_mbps} Mbps por {duracao_segundos} segundos. Log: {log_file_path}")

    # Comando iperf UDP:
    # -c <server_ip>: Servidor
    # -p <port>: Porta
    # -u: Modo UDP
    # -b <bandwidth>M: Largura de banda em Mbps
    # -t <duration>: Duração do teste
    # > log_file 2>&1: Redireciona stdout e stderr para o arquivo de log
    # &: Executa em segundo plano
    
    # O comando é executado diretamente no host Mininet via .cmd()
    cmd = (f"iperf3 -c {ip_servidor} -p {porta_servidor} -u -b {largura_banda_mbps}M -t {duracao_segundos} "
           f"> {log_file_path} 2>&1 &")
    
    host_cliente.cmd(cmd)
    
    print(f"[eMBB Gen] Comando iperf enviado para {host_cliente.name}. Aguardando conclusão...")
    
    # O script main (mininet_topologia_completa_v1) será responsável por esperar a duração.
    # Este script de geração apenas inicia o processo.

if __name__ == '__main__':
    # Este bloco é apenas para testes independentes do script, se necessário.
    # No contexto Mininet, essa função será chamada diretamente.
    print("Este script deve ser chamado a partir do ambiente Mininet.")
    print("Para um teste rápido (requer iperf instalado):")
    print("python3 gerador_trafego_embb.py <IP_SERVIDOR> <PORTA> <BANDA_MBPS> <DURACAO_S> <DIR_LOG>")

    if len(sys.argv) == 6:
        _ip_servidor = sys.argv[1]
        _porta_servidor = int(sys.argv[2])
        _largura_banda = int(sys.argv[3])
        _duracao = int(sys.argv[4])
        _log_dir = sys.argv[5]

        # Simulação de um host Mininet para teste
        class MockHost:
            def __init__(self, name="mock_host"):
                self.name = name
            def cmd(self, command):
                print(f"MockHost.cmd: {command}")
                # For a real test, you'd run this command directly in your shell
                os.system(command) 
        
        mock_h = MockHost()
        iniciar_trafego_embb(mock_h, _ip_servidor, _porta_servidor, _largura_banda, _duracao, _log_dir)
        print(f"Simulação concluída. Verifique {_log_dir}/iperf_embb_log.txt para o log.")
        time.sleep(_duracao + 5) # Espera para o iperf terminar
        print("Teste simulado finalizado.")
    else:
        print("Uso: python3 gerador_trafego_embb.py <IP_SERVIDOR> <PORTA> <BANDA_MBPS> <DURACAO_S> <DIR_LOG>")