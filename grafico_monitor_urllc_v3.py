import matplotlib
matplotlib.use("Agg")  # Usa backend sem GUI (ideal para servidores/headless)

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import pandas as pd
import numpy as np
import re

# --- Configuração ---
# O diretório do projeto deve ser o mesmo usado em mininet_topologia_completa_v3.py
project_dir = "/home/ubuntu/compartilhada"
arquivo_log_urllc = os.path.join(project_dir, "urllc_log.txt") # Ajustado para usar project_dir
arquivo_alerta = os.path.join(project_dir, "latencia.alerta") # Caminho para o arquivo de alerta de QoS

embb_client_name = "h_eMBB1"
embb_server_ip = "172.19.40.100" # IP do h_cloud
embb_log_base_dir = os.path.join(project_dir, "logs_embb") # Ajustado para usar project_dir
arquivo_log_embb = os.path.join(embb_log_base_dir, "iperf_embb_log.txt")

intervalo_ms = 1000  # 1 quadro por segundo (fps = 1)
window_size = 5 # Janela para a média móvel

# Listas para dados uRLLC
tempos_urllc = []
latencias_urllc = []

# Variáveis para o monitoramento de QoS
qos_active_start_index = None
qos_active_periods = [] # Lista de tuplas (start_index, end_index) para períodos de QoS ativo
first_qos_label = True # Flag para garantir que a label "QoS Ativo" apareça apenas uma vez

# Criar a figura e os eixos
fig, ax1 = plt.subplots(figsize=(12, 6)) # Aumentar tamanho para melhor visualização

# --- PRE-EXECUÇÃO: Garantir que os diretórios e arquivos de log existam ---
os.makedirs(project_dir, exist_ok=True)
os.makedirs(embb_log_base_dir, exist_ok=True)

if not os.path.exists(arquivo_log_urllc):
    print(f"Aviso: Arquivo de log uRLLC não encontrado: {arquivo_log_urllc}. Criando dummy.")
    with open(arquivo_log_urllc, "w") as f:
        f.write("Latência uRLLC: 2.5 ms\n")
        f.write("Latência uRLLC: 3.0 ms\n")
        f.write("Latência uRLLC: 2.8 ms\n")

if not os.path.exists(arquivo_log_embb):
    print(f"Aviso: Arquivo de log eMBB não encontrado: {arquivo_log_embb}. Criando dummy.")
    with open(arquivo_log_embb, "w") as f:
        f.write("[ 3] 0.0-1.0 sec  1.00 MBytes  8.0 Mbits/sec\n")
        f.write("[ 3] 1.0-2.0 sec  2.00 MBytes  16.0 Mbits/sec\n")
        f.write("[ 3] 2.0-3.0 sec  3.00 MBytes  24.0 Mbits/sec\n")

def extrair_latencias_urllc(linhas):
    latencias_extraidas = []
    for linha in linhas:
        if "Latência uRLLC" in linha:
            try:
                match = re.search(r'Latência uRLLC: (\d+\.\d+) ms', linha)
                if match:
                    latencias_extraidas.append(float(match.group(1)))
            except ValueError:
                continue
    return latencias_extraidas

def extrair_largura_banda_embb(linhas):
    larguras_banda_extraidas = []
    bandwidth_pattern = re.compile(r'(\d+\.\d+)\s+Mbits/sec')

    for linha in linhas:
        match = bandwidth_pattern.search(linha)
        if match:
            try:
                larguras_banda_extraidas.append(float(match.group(1)))
            except ValueError:
                continue
    return larguras_banda_extraidas


def atualizar(frame):
    global qos_active_start_index, qos_active_periods, first_qos_label

    # --- Ler e processar dados uRLLC ---
    try:
        with open(arquivo_log_urllc, "r") as f:
            linhas_urllc = f.readlines()
    except FileNotFoundError:
        print(f"Erro: Arquivo de log uRLLC não encontrado em {arquivo_log_urllc}. Skipping update.")
        return # Sair da atualização se o arquivo principal não existir

    nova_latencias = extrair_latencias_urllc(linhas_urllc)
    tempos_urllc.clear()
    latencias_urllc.clear()
    for i, lat in enumerate(nova_latencias):
        tempos_urllc.append(i)
        latencias_urllc.append(lat)

    current_data_index = len(tempos_urllc) - 1 if tempos_urllc else 0 # Ensure it's not negative

    # --- Monitoramento e marcação de QoS ---
    qos_is_active_now = os.path.exists(arquivo_alerta)

    if qos_is_active_now and qos_active_start_index is None:
        # QoS acaba de ser ativado
        qos_active_start_index = current_data_index

    elif not qos_is_active_now and qos_active_start_index is not None:
        # QoS acaba de ser desativado
        qos_active_periods.append((qos_active_start_index, current_data_index))
        qos_active_start_index = None

    # --- Plotar uRLLC (Eixo Y Esquerdo) ---
    ax1.clear()
    first_qos_label = True # Reset for each update call to correctly apply label

    # Plotar períodos de QoS ativo
    for start, end in qos_active_periods:
        if first_qos_label:
            ax1.axvspan(start, end, color='orange', alpha=0.3, label='QoS Ativo')
            first_qos_label = False
        else:
            ax1.axvspan(start, end, color='orange', alpha=0.3)

    # Plotar o período de QoS ativo atual (se houver)
    if qos_active_start_index is not None:
        if first_qos_label:
            ax1.axvspan(qos_active_start_index, current_data_index, color='orange', alpha=0.3, label='QoS Ativo')
            first_qos_label = False
        else:
            ax1.axvspan(qos_active_start_index, current_data_index, color='orange', alpha=0.3)


    ax1.plot(tempos_urllc, latencias_urllc, marker='o', color='blue', label="Latência uRLLC (ms)", linewidth=0.7, markersize=4)

    # Média móvel uRLLC
    if len(latencias_urllc) >= window_size:
        latencias_series = pd.Series(latencias_urllc)
        media_movel = latencias_series.rolling(window=window_size).mean()
        ax1.plot(tempos_urllc[window_size-1:], media_movel[window_size-1:], color='cyan', linestyle='--', label=f"Média Móvel uRLLC ({window_size}s)")

    ax1.axhline(y=5, color='red', linestyle=':', label='Limite uRLLC (5ms)')
    ax1.set_xlabel("Tempo (segundos/medidas)")
    ax1.set_ylabel("Latência uRLLC (ms)", color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    # Ajustar o limite Y para garantir que 5ms e os dados caibam
    if latencias_urllc:
        ax1.set_ylim(0, max(10, max(latencias_urllc + [5]) + 1))
    else:
        ax1.set_ylim(0, 10)
    ax1.grid(True, linestyle='--', alpha=0.7)


    # --- Títulos e Legendas ---
    ax1.set_title("Monitoramento de Latência uRLLC")

    # Combinar legendas de ambos os eixos
    lines, labels = ax1.get_legend_handles_labels()
    ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(0.0, 1.0))

    # Salvar como PNG em alta definição (DPI)
    plt.savefig(os.path.join(project_dir, "latencia_e_trafego.png"), dpi=600, bbox_inches='tight')


# Criar a animação (com 10 quadros como exemplo para testes, em Mininet pode ser mais)
# Em um ambiente Mininet real, o 'frames' pode ser omitido ou muito maior para captura contínua.
# Ou você pode rodar 'atualizar(None)' periodicamente em vez de FuncAnimation.
ani = animation.FuncAnimation(
    fig,
    atualizar,
    frames=120,  # número de quadros do vídeo/gif para demonstração
    interval=intervalo_ms,
    cache_frame_data=False
)

# Salvar como GIF
ani.save(os.path.join(project_dir, "latencia_e_trafego.gif"), writer="pillow", fps=1)

# Salvar como MP4 (vídeo)
try:
    ani.save(os.path.join(project_dir, "latencia_e_trafego.mp4"), writer="ffmpeg", fps=1)
except ValueError as e:
    print(f"Não foi possível salvar o MP4: {e}. Certifique-se de que o ffmpeg está instalado e acessível.")

print("✅ PNG, GIF e MP4 gerados com sucesso para latência uRLLC e tráfego eMBB!")