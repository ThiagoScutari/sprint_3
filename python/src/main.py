import logging
from db_manager import DatabaseManager
import analise_dados as ad

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def exibir_menu():
    print("\n=== MENU PRINCIPAL ===")
    print("1 - Exibir análise: folhas por ordem de produção")
    print("2 - Exibir análise: produtividade por máquina")
    print("3 - Exibir análise: folhas por dia")
    print("4 - Exportar CSV/JSON")
    print("5 - Visualizar gráfico: folhas por ordem")
    print("6 - Visualizar gráfico: produtividade por máquina")
    print("7 - Visualizar gráfico: folhas por dia")
    print("0 - Sair")

def main():
    db = DatabaseManager()
    df = ad.carregar_dados(db)

    if df.empty:
        logging.warning("Nenhum dado encontrado no banco.")
        return

    while True:
        exibir_menu()
        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            resultado = ad.folhas_por_ordem(df)
            print(resultado.to_string(index=False))

        elif opcao == '2':
            resultado = ad.produtividade_por_maquina(df)
            print(resultado.to_string(index=False))

        elif opcao == '3':
            resultado = ad.folhas_por_dia(df)
            print(resultado.to_string(index=False))

        elif opcao == '4':
            ad.exportar_para_csv(df, "leituras.csv")
            ad.exportar_para_json(df, "leituras.json")

        elif opcao == '5':
            resumo = ad.folhas_por_ordem(df)
            ad.plot_folhas_por_ordem_plotly(resumo)

        elif opcao == '6':
            resumo = ad.produtividade_por_maquina(df)
            ad.plot_produtividade_maquina_plotly(resumo)

        elif opcao == '7':
            resumo = ad.folhas_por_dia(df)
            ad.plot_folhas_por_dia_plotly(resumo)

        elif opcao == '0':
            print("Encerrando...")
            break

        else:
            print("Opção inválida.")

    db.fechar()


if __name__ == "__main__":
    main()
