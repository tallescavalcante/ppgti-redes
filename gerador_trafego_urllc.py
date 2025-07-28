import subprocess
import time
import os

def iniciar_trafego_urllc(h_cliente, ip_servidor, porta_urllc, duracao_segundos, log_dir):
    """
    Inicia um cliente iperf3 para gerar tráfego uRLLC (UDP) com taxa de bits baixa.
    """
    print(f"*** Iniciando tráfego uRLLC de {h_cliente.name} para {ip_servidor}:{porta_urllc}...")

    log_file_path = os.path.join(log_dir, f"iperf_urllc_{h_cliente.name}_to_{ip_servidor}.log")

    # Comando iperf3 para tráfego UDP de baixo bitrate (e.g., 100 Kbps)
    # -u: UDP
    # -b: Largura de banda em bits/seg (ex: 100k para 100 Kbps)
    # -t: Duração em segundos
    # -i: Intervalo para relatórios (opcional, pode ser omitido para menos saída)
    # --logfile: Salva a saída para um arquivo
    # -p: Porta
    iperf_cmd = (
        f"iperf3 -c {ip_servidor} -b 40M -l 128 -t {duracao_segundos} -p {porta_urllc} "
        f"--logfile {log_file_path} > /dev/null 2>&1 &"
    )
    
    print(f"    - Executando em {h_cliente.name}: {iperf_cmd}")
    h_cliente.cmd(iperf_cmd)
    print(f"    - Tráfego uRLLC de {h_cliente.name} iniciado.")

if __name__ == '__main__':
    # Este bloco é para testes independentes ou demonstração.
    # Em uma topologia Mininet, esta função seria chamada diretamente.
    print("Este script é destinado a ser importado e chamado por um script Mininet.")
    print("Exemplo de uso (requer um host e servidor iperf3 rodando):")
    print("  # Simula um host Mininet para demonstração")
    # from mininet.node import Host
    # class MockHost:
    #     def __init__(self, name):
    #         self.name = name
    #     def cmd(self, command):
    #         print(f"MockHost {self.name} received command: {command}")
    #
    # mock_h_uRLLC1 = MockHost('h_uRLLC1')
    # mock_ip_cloud = '127.0.0.1' # Apenas para demonstração
    # mock_porta = 8080
    # mock_duracao = 10
    # mock_log_dir = './logs_urllc_test'
    # os.makedirs(mock_log_dir, exist_ok=True)
    # iniciar_trafego_urllc(mock_h_uRLLC1, mock_ip_cloud, mock_porta, mock_duracao, mock_log_dir)
    # print("Verifique o diretório 'logs_urllc_test' para o log.")