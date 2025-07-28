#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Host, Node, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time
import os
from threading import Thread

# Importar o nosso novo controlador
import controlador_qos
# Importar o novo gerador de tráfego eMBB
import gerador_trafego_embb
# ### ALTERAÇÕES PARA ULLRC ###
import gerador_trafego_urllc # Importar o novo gerador de tráfego uRLLC


class LinuxRouter(Node):
    """Um Nó que se comporta como um roteador Linux."""
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')
        info(f"*** Encaminhamento de IP habilitado em {self.name}\n")

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

def run_topology():
    # Defina o diretório do seu projeto aqui. Baseado na sua imagem.
    project_dir = "/home/ubuntu/compartilhada"
    alert_file_path = os.path.join(project_dir, "latencia.alerta")
    embb_log_dir = os.path.join(project_dir, "logs_embb")
    # ### ALTERAÇÕES PARA ULLRC ###
    urllc_log_dir = os.path.join(project_dir, "logs_urllc") # Novo diretório para logs uRLLC


    # Limpa o ficheiro de alerta de uma execução anterior, se existir
    if os.path.exists(alert_file_path):
        os.remove(alert_file_path)
    
    # Limpa o diretório de logs eMBB, se existir
    if os.path.exists(embb_log_dir):
        import shutil
        shutil.rmtree(embb_log_dir)
    os.makedirs(embb_log_dir, exist_ok=True)
        
    # ### ALTERAÇÕES PARA ULLRC ###
    # Limpa o diretório de logs uRLLC, se existir
    if os.path.exists(urllc_log_dir):
        import shutil
        shutil.rmtree(urllc_log_dir)
    os.makedirs(urllc_log_dir, exist_ok=True)
        
    net = Mininet(switch=OVSKernelSwitch, link=TCLink, controller=None)

    info('*** Adicionando Roteadores da Rede de Transporte...\n')
    r_trans1 = net.addHost('r_trans1', cls=LinuxRouter, ip=None)
    r_trans2 = net.addHost('r_trans2', cls=LinuxRouter, ip=None)
    r_trans3 = net.addHost('r_trans3', cls=LinuxRouter, ip=None)
    r_trans4 = net.addHost('r_trans4', cls=LinuxRouter, ip=None)
    
    roteadores = [r_trans1, r_trans2, r_trans3, r_trans4]

    info('*** Adicionando Switches de Acesso...\n')
    s_access1 = net.addSwitch('s_access1')
    s_access2 = net.addSwitch('s_access2')

    info('*** Adicionando Hosts de Usuário e Nuvem...\n')
    h_uRLLC1 = net.addHost('h_uRLLC1', ip='172.18.1.10/24', defaultRoute='via 172.18.1.1')
    h_eMBB1 = net.addHost('h_eMBB1', ip='172.18.1.20/24', defaultRoute='via 172.18.1.1')
    h_uRLLC2 = net.addHost('h_uRLLC2', ip='172.18.2.10/24', defaultRoute='via 172.18.2.1')
    h_eMBB2 = net.addHost('h_eMBB2', ip='172.18.2.20/24', defaultRoute='via 172.18.2.1')
    h_cloud = net.addHost('h_cloud', ip='172.19.40.100/24', defaultRoute='via 172.19.40.4')
    
    link_params_access = {'bw': 50}
    link_params_transport = {'bw': 100}
    link_params_cloud = {'bw': 200}

    info('*** Criando Links...\n')
    net.addLink(h_uRLLC1, s_access1, **link_params_access)
    net.addLink(h_eMBB1, s_access1, **link_params_access)
    net.addLink(h_uRLLC2, s_access2, **link_params_access)
    net.addLink(h_eMBB2, s_access2, **link_params_access)
    net.addLink(s_access1, r_trans1, intfName2='r_trans1-eth0', **link_params_access)
    net.addLink(s_access2, r_trans2, intfName2='r_trans2-eth0', **link_params_access)
    net.addLink(r_trans1, r_trans3, intfName1='r_trans1-eth1', intfName2='r_trans3-eth0', **link_params_transport)
    net.addLink(r_trans2, r_trans3, intfName1='r_trans2-eth1', intfName2='r_trans3-eth1', **link_params_transport)
    net.addLink(r_trans3, r_trans4, intfName1='r_trans3-eth2', intfName2='r_trans4-eth0', **link_params_transport)
    net.addLink(r_trans4, h_cloud, intfName1='r_trans4-eth1', **link_params_cloud)

    info('*** Iniciando a rede...\n')
    net.start()

    info('*** Configurando modo standalone para switches OVS...\n')
    for sw in net.switches:
        sw.cmd('ovs-vsctl set-fail-mode', sw.name, 'standalone')

    info('*** Configurando IPs e Rotas nos Roteadores...\n')
    r_trans1.cmd('ip addr add 172.18.1.1/24 dev r_trans1-eth0'); r_trans1.cmd('ip link set r_trans1-eth0 up')
    r_trans1.cmd('ip addr add 172.19.13.1/24 dev r_trans1-eth1'); r_trans1.cmd('ip link set r_trans1-eth1 up')
    r_trans2.cmd('ip addr add 172.18.2.1/24 dev r_trans2-eth0'); r_trans2.cmd('ip link set r_trans2-eth0 up')
    r_trans2.cmd('ip addr add 172.19.23.2/24 dev r_trans2-eth1'); r_trans2.cmd('ip link set r_trans2-eth1 up')
    r_trans3.cmd('ip addr add 172.19.13.3/24 dev r_trans3-eth0'); r_trans3.cmd('ip link set r_trans3-eth0 up')
    r_trans3.cmd('ip addr add 172.19.23.3/24 dev r_trans3-eth1'); r_trans3.cmd('ip link set r_trans3-eth1 up')
    r_trans3.cmd('ip addr add 172.19.34.3/24 dev r_trans3-eth2'); r_trans3.cmd('ip link set r_trans3-eth2 up')
    r_trans4.cmd('ip addr add 172.19.34.4/24 dev r_trans4-eth0'); r_trans4.cmd('ip link set r_trans4-eth0 up')
    r_trans4.cmd('ip addr add 172.19.40.4/24 dev r_trans4-eth1'); r_trans4.cmd('ip link set r_trans4-eth1 up')
    r_trans1.cmd('ip route add 172.18.2.0/24 via 172.19.13.3'); r_trans1.cmd('ip route add 172.19.23.0/24 via 172.19.13.3'); r_trans1.cmd('ip route add 172.19.34.0/24 via 172.19.13.3'); r_trans1.cmd('ip route add 172.19.40.0/24 via 172.19.13.3')
    r_trans2.cmd('ip route add 172.18.1.0/24 via 172.19.23.3'); r_trans2.cmd('ip route add 172.19.13.0/24 via 172.19.23.3'); r_trans2.cmd('ip route add 172.19.34.0/24 via 172.19.23.3'); r_trans2.cmd('ip route add 172.19.40.0/24 via 172.19.23.3')
    r_trans3.cmd('ip route add 172.18.1.0/24 via 172.19.13.1'); r_trans3.cmd('ip route add 172.18.2.0/24 via 172.19.23.2'); r_trans3.cmd('ip route add 172.19.40.0/24 via 172.19.34.4')
    r_trans4.cmd('ip route add 172.18.1.0/24 via 172.19.34.3'); r_trans4.cmd('ip route add 172.18.2.0/24 via 172.19.34.3'); r_trans4.cmd('ip route add 172.19.13.0/24 via 172.19.34.3'); r_trans4.cmd('ip route add 172.19.23.0/24 via 172.19.34.3')

    info('*** Aguardando para estabilização da rede...\n')
    time.sleep(2)
    
    info('*** Iniciando o Controlador de QoS em uma thread separada...\n')
    controller_thread = Thread(target=controlador_qos.iniciar_loop_controle, args=(roteadores, project_dir, net))
    controller_thread.daemon = True
    controller_thread.start()
    
    info('*** Iniciando o Monitor de Latência uRLLC...\n')
    monitor_cmd = (f"cd {project_dir} && "
                   f"sudo python3 -u gerador_monitor_uRLLC.py > urllc_log.txt &")
    h_uRLLC1.cmd(monitor_cmd)
    
    info('*** Iniciando Servidor iperf para tráfego eMBB...\n')
    h_cloud.cmd(f'iperf3 -s -p {controlador_qos.porta_embb} &') # Use iperf3
    
    # ### ALTERAÇÕES PARA ULLRC ###
    info('*** Iniciando Servidor iperf para tráfego uRLLC...\n')
    # Usamos a porta definida no controlador para consistência
    h_cloud.cmd(f'iperf3 -s -p {controlador_qos.porta_urllc} &') # Servidor UDP para uRLLC

    info('*** Aguardando 3 segundos para os servidores iperf iniciarem...\n')
    time.sleep(2)

    # --- INÍCIO DA CHAMADA AO GERADOR DE TRÁFEGO eMBB SEPARADO ---
    info('*** Iniciando Cliente iperf para tráfego eMBB (45 Mbits/s por 120s)\n')
    largura_banda_embb = 45 # Mbits/s
    duracao_testes = 120    # Segundos (duração total para eMBB e uRLLC)
    
    gerador_trafego_embb.iniciar_trafego_embb(
        h_eMBB1,
        h_cloud.IP(),
        controlador_qos.porta_embb,
        largura_banda_embb,
        duracao_testes, # Usar a mesma duração para ambos os testes
        embb_log_dir
    )
    
    # ### ALTERAÇÕES PARA ULLRC ###
    info('*** Iniciando Cliente iperf para tráfego uRLLC\n')
    # O gerador de tráfego uRLLC simula um fluxo constante de baixa taxa de bits
    gerador_trafego_urllc.iniciar_trafego_urllc(
        h_uRLLC2, # Usar o mesmo host que monitora a latência
        h_cloud.IP(),
        controlador_qos.porta_urllc,
        duracao_testes, # Usar a mesma duração
        urllc_log_dir # Novo diretório de log para uRLLC
    )

    # --- INICIAR GERADOR DE GRÁFICO AUTOMATICAMENTE ---
    info('*** Iniciando o gerador de gráfico uRLLC/eMBB automaticamente...\n')
    graph_cmd = (f"cd {project_dir} && "
                 f"sudo python3 -u grafico_monitor_urllc_v3.py > graph_gen_log.txt 2>&1 &")
    h_uRLLC1.cmd(graph_cmd)
    
    info('*** Tráfego eMBB, uRLLC e Gerador de Gráfico iniciados. Aguardando conclusão do teste...\n')

    # Espera o tempo necessário para o tráfego eMBB, uRLLC e a geração do gráfico terminarem
    time.sleep(duracao_testes + 10)
    info('*** Teste de tráfego eMBB e geração de gráfico concluídos.\n')

    #info('*** Topologia pronta. Teste a conectividade no CLI.\n')
    CLI(net)

    info('*** Parando a rede...\n')

    net.stop()
    if os.path.exists(alert_file_path):
        os.remove(alert_file_path)
    # Não remove os diretórios de logs para análise pós-execução
    # if os.path.exists(embb_log_dir):
    #     import shutil
    #     shutil.rmtree(embb_log_dir)
    # if os.path.exists(urllc_log_dir): # ### ALTERAÇÕES PARA ULLRC ###
    #     import shutil
    #     shutil.rmtree(urllc_log_dir)


if __name__ == '__main__':
    setLogLevel('info')
    run_topology()