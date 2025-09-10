import serial
import time
import logging
from datetime import datetime
from db_manager import DatabaseManager

# Configurações
PORTA_SERIAL = 'rfc2217://localhost:4000'
COD_MAQUINA = 'maq002'
ORDEM_PRODUCAO = 'OP00221'
INTERVALO_SEGUNDOS = 0.2
LIMITE_SUPERIOR = 300   # cm
LIMITE_INFERIOR = 10    # cm

# Estado da leitura
estado = {
    "ultima_posicao": "inicio",
    "folhas": 0
}

# Logger configurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def detectar_folha(distancia, estado):
    if estado["ultima_posicao"] == "inicio" and distancia >= LIMITE_SUPERIOR:
        estado["ultima_posicao"] = "subindo"
    elif estado["ultima_posicao"] == "subindo" and distancia <= LIMITE_INFERIOR:
        estado["ultima_posicao"] = "descendo"
        estado["folhas"] += 1
        logging.info(f" Nova folha registrada! Total: {estado['folhas']}")
    elif estado["ultima_posicao"] == "descendo" and distancia >= LIMITE_SUPERIOR:
        estado["ultima_posicao"] = "subindo"
    return estado["folhas"]

def processar_linha(linha, estado, db):
    try:
        if ',' in linha:
            dataHora_str, distancia_str = linha.split(',')
            dataHora = datetime.strptime(dataHora_str.strip(), "%Y-%m-%d %H:%M:%S")
            distancia = float(distancia_str.strip())

            folhas = detectar_folha(distancia, estado)

            logging.info(f"[{dataHora}]  {distancia:.1f} cm | OP={ORDEM_PRODUCAO} | folhas={folhas}")

            db.inserir_leitura(
                codMaquina=COD_MAQUINA,
                ordemProducao=ORDEM_PRODUCAO,
                dataHora=dataHora.strftime("%Y-%m-%d %H:%M:%S"),
                distancia=distancia,
                folhas=folhas
            )
    except Exception as e:
        logging.warning(f" Erro ao processar linha '{linha.strip()}': {e}")

def monitorar_sensor():
    logging.info(" Iniciando monitoramento do sensor...")

    try:
        with serial.serial_for_url(PORTA_SERIAL, baudrate=115200, timeout=1) as ser, \
             DatabaseManager("../database/enfesto.db") as db:

            logging.info(" Conectado ao sensor via RFC2217")
            logging.info(" Monitorando sensor...\n")

            while True:
                linha = ser.readline().decode('utf-8').strip()
                if linha:
                    processar_linha(linha, estado, db)
                time.sleep(INTERVALO_SEGUNDOS)

    except KeyboardInterrupt:
        logging.info("\n Monitoramento encerrado pelo usuário.")
    except Exception as e:
        logging.exception("Erro inesperado durante execução:")

if __name__ == '__main__':
    monitorar_sensor()
