#  Sistema de Monitoramento de Enfesto em Indústrias Têxteis

##  Grupo: 44

### 👨‍💻 Integrantes:

* Thiago Scutari - RM562831 | [thiago.scutari@outlook.com](mailto:thiago.scutari@outlook.com)
* Henrique Ribeiro Siqueira - RM565044 | [henrique.ribeiro1201@gmail.com](mailto:henrique.ribeiro1201@gmail.com)
* Mariana Cavalante Oliveira - RM561678 | [mari.kvalcant@gmail.com](mailto:mari.kvalcant@gmail.com)

### 👩‍🏫 Professores:

* Leonardo Ruiz Orabona
* Andre Godoi Chiovato

---

# 📦 Sistema de Monitoramento de Enfestos com ESP32 + Python + SQLite

Projeto completo de simulação e análise de um sistema de monitoramento de **folhas de tecido (enfesto)**, utilizando sensores simulados com ESP32, banco de dados local em SQLite, análise em Python, gráficos interativos com Plotly e exportação de relatórios.

---

## Objetivo

Simular um processo industrial de **movimentação de tecido**, em que um sensor ultrassônico mede a distância em tempo real e, com isso, identificamos **quantas folhas foram passadas** (ida e volta da máquina).

---

## Componentes do Projeto

- **ESP32 (simulado via Wokwi)** com sensor ultrassônico
- **Leitura contínua dos dados via porta serial (RFC2217)**
- **Registro das leituras em SQLite (enfesto.db)**
- **Detecção de folhas (ida e volta) com base nos limites de distância**
- **Armazenamento de data/hora, máquina e ordem de produção**
- **Análises com Pandas + gráficos com Plotly**
- **Exportação para CSV e JSON**
- **Interface CLI interativa com `main.py`**

---

## 📂 Estrutura do Projeto

```
SPRINT_2/
├── docs/
├── ESP32_Firmware/
├── python/
│   ├── assets/
│   ├── database/
│   │   └── enfesto.db
│   ├── src/
│   │   ├── analise_dados.py
│   │   ├── db_manager.py
│   │   ├── main.py
│   │   └── monitorar_sensor.py
│   └── output/
│       └── (CSV e JSON gerados)
├── requirements.txt
└── README.md
```

---

## Requisitos

- Python 3.10+
- pip
- Ambiente virtual recomendado (`venv`)

---

## Instalação

```bash
# Clone o projeto
git clone <repositorio>

# Acesse a pasta Python
cd python

# Crie ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

---

## Execução

### 1. Inicie a simulação no Wokwi (sensor conectado à porta RFC2217)

### 2. Rode o script de monitoramento:

```bash
python src/monitorar_sensor.py
```

O sensor começará a registrar distância + hora + OP + máquina e armazenar no banco.

### 3. Rode a análise e relatórios:

```bash
python src/main.py
```

Você poderá:
- Visualizar folhas por ordem
- Ver produtividade por máquina
- Exportar CSV/JSON
- Abrir gráficos interativos (Plotly)

---

## Funcionalidades disponíveis via `main.py`

| Opção | Ação |
|-------|------|
| 1 | Análise: folhas por ordem de produção |
| 2 | Análise: produtividade por máquina |
| 3 | Análise: folhas por dia |
| 4 | Exportar dados para CSV e JSON |
| 5 | Gráfico: folhas por OP (Plotly) |
| 6 | Gráfico: produtividade por máquina (Plotly) |
| 7 | Gráfico: folhas por dia (Plotly) |
| 0 | Sair |

---

## Exemplo de Registro

```
[2025-06-13 21:52:45]  399.9 cm | OP=OP00123 | folhas=4
Nova folha registrada! Total: 5
```

---

## 📚 Bibliotecas Utilizadas

- `sqlite3` – Banco de dados local
- `pandas` – Manipulação de dados
- `plotly` – Visualizações interativas
- `serial` – Comunicação com sensor simulado
- `logging` – Log de eventos e rastreamento
