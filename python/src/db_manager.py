import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='../database/enfesto.db'):
        self.db_path = db_path
        self.conexao = sqlite3.connect(self.db_path)
        self.cursor = self.conexao.cursor()
        self.__criar_tabela()
        print(f"Banco conectado em: {self.db_path}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fechar()

    def __criar_tabela(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codMaquina TEXT NOT NULL,
                    ordemProducao TEXT NOT NULL,
                    dataHora TEXT NOT NULL,
                    distancia REAL NOT NULL,
                    folhas INTEGER NOT NULL
                )
            ''')
            self.conexao.commit()
            print("Tabela 'leituras' verificada/criada com sucesso.")
        except sqlite3.Error as e:
            print(f"Erro ao criar tabela: {e}")

    def inserir_leitura(self, codMaquina, ordemProducao, dataHora, distancia, folhas):
        try:
            self.cursor.execute('''
                INSERT INTO leituras (codMaquina, ordemProducao, dataHora, distancia, folhas)
                VALUES (?, ?, ?, ?, ?)
            ''', (codMaquina, ordemProducao, dataHora, distancia, folhas))
            self.conexao.commit()
            print(f"Leitura inserida com sucesso: {codMaquina} | OP={ordemProducao} | {distancia}cm | folhas={folhas}")
        except sqlite3.Error as e:
            print(f"Erro ao inserir leitura: {e}")

    def buscar_leituras(self):
        try:
            self.cursor.execute('SELECT * FROM leituras')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar leituras: {e}")
            return []

    def buscar_por_maquina(self, codMaquina):
        try:
            self.cursor.execute('SELECT * FROM leituras WHERE codMaquina = ?', (codMaquina,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar por máquina: {e}")
            return []

    def buscar_por_ordem(self, ordemProducao):
        try:
            self.cursor.execute('SELECT * FROM leituras WHERE ordemProducao = ?', (ordemProducao,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar por ordem: {e}")
            return []

    def buscar_por_data_range(self, data_inicio, data_fim):
        try:
            self.cursor.execute('''
                SELECT * FROM leituras
                WHERE datetime(dataHora) BETWEEN datetime(?) AND datetime(?)
            ''', (data_inicio, data_fim))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao buscar por período: {e}")
            return []

    def atualizar_leitura(self, id, distancia, folhas):
        try:
            self.cursor.execute('''
                UPDATE leituras
                SET distancia = ?, folhas = ?
                WHERE id = ?
            ''', (distancia, folhas, id))
            self.conexao.commit()
            print(f"Leitura atualizada (ID={id}) com novos dados.")
        except sqlite3.Error as e:
            print(f"Erro ao atualizar leitura: {e}")

    def deletar_leitura(self, id):
        try:
            self.cursor.execute('DELETE FROM leituras WHERE id = ?', (id,))
            self.conexao.commit()
            print(f"Leitura deletada (ID={id}).")
        except sqlite3.Error as e:
            print(f"Erro ao deletar leitura: {e}")

    def fechar(self):
        try:
            self.conexao.close()
            print("Conexão com banco encerrada.")
        except sqlite3.Error as e:
            print(f"Erro ao fechar conexão: {e}")
