import time
import os

# --- Configurações ---
intervalo_verificacao = 5 # Segundos
porta_urllc = 5202
porta_embb = 5201 # Porta padrão do iperf

# Flag para saber se as regras de QoS já foram aplicadas
regras_qos_ativas = False

def aplicar_regras_qos_bidirecional(roteadores, net):
    """Aplica regras de QoS HTB+SFQ para garantir baixa latência."""
    print(">>> ALERTA DETETADO! Aplicando regras de QoS FINAIS (HTB+SFQ)...")
    
    interfaces_map = {
        'r_trans1': { 'forward': ['r_trans1-eth1'], 'backward': ['r_trans1-eth0'] },
        'r_trans2': { 'forward': ['r_trans2-eth1'], 'backward': ['r_trans2-eth0'] },
        'r_trans3': { 'forward': ['r_trans3-eth2'], 'backward': ['r_trans3-eth0', 'r_trans3-eth1'] },
        'r_trans4': { 'forward': ['r_trans4-eth1'], 'backward': ['r_trans4-eth0'] }
    }

    for roteador in roteadores:
        if roteador.name not in interfaces_map:
            continue
        for nome_iface in interfaces_map[roteador.name].get('forward', []):
            aplicar_htb_sfq_em_interface(roteador, nome_iface, 'dport')
        for nome_iface in interfaces_map[roteador.name].get('backward', []):
            aplicar_htb_sfq_em_interface(roteador, nome_iface, 'sport')
    
    print("    - Regras de QoS finais aplicadas. A estabilizar a rede...")
    try:
        h_uRLLC1 = net.get('h_uRLLC1')
        h_uRLLC1.cmdPrint('ping -c 1 172.18.1.1')
    except Exception as e:
        print(f"    - Aviso: Falha ao executar ping de estabilização: {e}")
        
    print("    - Rede estabilizada.")
            
    return True

def aplicar_htb_sfq_em_interface(roteador, nome_iface, direcao_filtro):
    """Função auxiliar para aplicar a lógica HTB+SFQ numa interface."""
    iface = roteador.intf(nome_iface)
    if not iface: return

    print(f"    - Aplicando regras em {roteador.name}-{iface.name} (filtro por {direcao_filtro})")
    
    bw = iface.params.get('bw', 100)
    if bw is None: bw = 100
    rate_mbit = int(bw * 0.95)

    cmds = [
        f'tc qdisc del dev {iface.name} root 2> /dev/null',
        # 1. Adiciona a qdisc HTB principal
        f'tc qdisc add dev {iface.name} root handle 1: htb default 30',
        # 2. Adiciona a classe pai
        f'tc class add dev {iface.name} parent 1: classid 1:1 htb rate {rate_mbit}mbit',
        
        # 3. Adiciona as classes filhas para cada tipo de tráfego
        f'tc class add dev {iface.name} parent 1:1 classid 1:10 htb rate 5mbit ceil 20mbit prio 1',
        f'tc class add dev {iface.name} parent 1:1 classid 1:20 htb rate 10mbit ceil 15mbit prio 2',
        f'tc class add dev {iface.name} parent 1:1 classid 1:30 htb rate 1mbit ceil 5mbit prio 3',

        # --- LÓGICA FINAL ---
        # 4. Anexa uma qdisc SFQ a cada classe HTB para evitar bufferbloat dentro da classe.
        f'tc qdisc add dev {iface.name} parent 1:10 handle 10: sfq perturb 10',
        f'tc qdisc add dev {iface.name} parent 1:20 handle 20: sfq perturb 10',
        f'tc qdisc add dev {iface.name} parent 1:30 handle 30: sfq perturb 10',
        
        # 5. Adiciona os filtros para direcionar o tráfego para as classes HTB corretas
        f'tc filter add dev {iface.name} protocol ip parent 1:0 prio 1 u32 match ip protocol 1 0xff flowid 1:10',
        f'tc filter add dev {iface.name} protocol arp parent 1:0 prio 1 flowid 1:10',
        f'tc filter add dev {iface.name} protocol ip parent 1:0 prio 1 u32 match ip {direcao_filtro} {porta_urllc} 0xffff flowid 1:10',
        f'tc filter add dev {iface.name} protocol ip parent 1:0 prio 2 u32 match ip {direcao_filtro} {porta_embb} 0xffff flowid 1:20'
    ]
    for cmd in cmds:
        roteador.cmd(cmd)


def remover_regras_qos(roteadores):
    """Remove as regras de QoS de todas as interfaces, voltando ao padrão."""
    print("<<< LATÊNCIA NORMALIZADA. Removendo regras de QoS...")
    for roteador in roteadores:
        interfaces = [iface for iface in roteador.intfList() if 'lo' not in str(iface)]
        for iface in interfaces:
            print(f"    - Removendo regras de {roteador.name}-{iface.name}")
            roteador.cmd(f'tc qdisc del dev {iface.name} root 2>/dev/null')
    return False

def iniciar_loop_controle(roteadores_para_controlar, project_dir, net):
    """Loop principal que monitoriza o alerta e aciona o controlo."""
    global regras_qos_ativas
    
    arquivo_alerta = os.path.join(project_dir, "latencia.alerta")
    
    print("Controlador de QoS iniciado.")
    try:
        while True:
            if os.path.exists(arquivo_alerta):
                if not regras_qos_ativas:
                    regras_qos_ativas = aplicar_regras_qos_bidirecional(roteadores_para_controlar, net)
            else:
                if regras_qos_ativas:
                    regras_qos_ativas = remover_regras_qos(roteadores_para_controlar)
            
            time.sleep(intervalo_verificacao)
    except KeyboardInterrupt:
        print("\nParando loop de controlo.")
        if regras_qos_ativas:
            remover_regras_qos(roteadores_para_controlar)

if __name__ == '__main__':
    print("Este script deve ser importado.")
