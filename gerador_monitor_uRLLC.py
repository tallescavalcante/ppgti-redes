import subprocess
import time
import os
import re

# --- Configurações ---
ip_destino = "172.19.40.100"  # IP do h_cloud
intervalo_segundos = 1       # Intervalo entre pings
arquivo_alerta = "latencia.alerta"
limiar_latencia_ms = 5.0     # Latência alvo para uRLLC
periodo_normalizacao_segundos = 70

tempo_primeira_latencia_ok = 0

def obter_latencia_ping(ip):
    try:
        # Executa 1 ping, retorna apenas a linha com "time="
        resultado = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True, text=True
        )
        output = resultado.stdout
        match = re.search(r'time=(\d+(\.\d+)?) ms', output)
        if match:
            return float(match.group(1))  # latência em ms
        else:
            return -1  # Falha no ping
    except Exception as e:
        print(f"[Erro] Falha ao executar ping: {e}")
        return -1

print(f"Iniciando monitoramento uRLLC com ping para {ip_destino} (limite: {limiar_latencia_ms} ms)")
try:
    while True:
        latencia_ms = obter_latencia_ping(ip_destino)
        
        if latencia_ms >= 0:
            print(f"[INFO] Latência uRLLC: {latencia_ms:.2f} ms")

            if latencia_ms > limiar_latencia_ms:
                if not os.path.exists(arquivo_alerta):
                    print(f"[ALERTA] Latência {latencia_ms:.2f} ms > {limiar_latencia_ms:.2f} ms. Criando arquivo de alerta.")
                    with open(arquivo_alerta, "w") as f:
                        f.write(f"{latencia_ms:.2f}")
                tempo_primeira_latencia_ok = 0
            else:
                if os.path.exists(arquivo_alerta):
                    if tempo_primeira_latencia_ok == 0:
                        print(f"[INFO] Latência abaixo do limiar. Iniciando período de calma de {periodo_normalizacao_segundos}s...")
                        tempo_primeira_latencia_ok = time.time()
                    elif time.time() - tempo_primeira_latencia_ok > periodo_normalizacao_segundos:
                        print("[INFO] Período de calma concluído. Removendo arquivo de alerta.")
                        os.remove(arquivo_alerta)
                        tempo_primeira_latencia_ok = 0
        else:
            print("[WARN] Timeout no ping ou resposta inválida.")
            tempo_primeira_latencia_ok = 0

        time.sleep(intervalo_segundos)

except KeyboardInterrupt:
    print("\nMonitoramento uRLLC encerrado.")
    if os.path.exists(arquivo_alerta):
        os.remove(arquivo_alerta)