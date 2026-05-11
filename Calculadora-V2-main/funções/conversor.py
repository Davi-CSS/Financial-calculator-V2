import requests
from datetime import datetime, timedelta

def obter_cotacao_antiga(data_str):
    """
    data_str: data no formato 'dd/mm/aaaa'
    retorna: valor da cotação do dólar (float) ou None se não encontrado
    """
    try:
        data = datetime.strptime(data_str,"%d/%m/%Y")
        data_formatada = data.strftime("%Y%m%d")
        url = f'https://economia.awesomeapi.com.br/json/daily/USD-BRL/1?start_date={data_formatada}&end_date={data_formatada}'
        resposta = requests.get(url)
        dados = resposta.json()
        if isinstance(dados, list) and len(dados) > 0:
            return float(dados[0]["bid"])
        return None  # não encontrou para o dia exato
    except Exception as e:
        print("Erro ao obter cotação antiga:", e)
        return None

def obter_cotacao_atual():
    """
    Retorna a cotação atual do dólar (float) ou None se não conseguir buscar.
    """
    import requests
    try:
        url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        if "USDBRL" in dados and "bid" in dados["USDBRL"]:
            return float(dados["USDBRL"]["bid"])
        else:
            print("Resposta inesperada da API:", dados)
            return None
    except Exception as e:
        print("Erro ao obter cotação atual:", e)
        return None

def simular_investimento_dolar():
    data = input("Digite a data da compra do dólar (dd/mm/aaaa): ")
    try:
        valor_usd = float(input("Digite o valor investido em dólar: "))
    except ValueError:
        print("Valor investido inválido.")
        return

    cotacao_antiga = obter_cotacao_antiga(data)
    if cotacao_antiga is None:
        print("Não foi possível encontrar a cotação para essa data ou para os 7 dias anteriores.")
        return

    cotacao_atual = obter_cotacao_atual()
    if cotacao_atual is None:
        print("Não foi possível obter a cotação atual.")
        return

    valor_investido_reais = valor_usd * cotacao_antiga
    valor_hoje_reais = valor_usd * cotacao_atual
    lucro = valor_hoje_reais - valor_investido_reais
    percentual = (lucro / valor_investido_reais) * 100

    print(f"\nCotação em {data}: R$ {cotacao_antiga:.2f}")
    print(f"Cotação atual: R$ {cotacao_atual:.2f}")
    print(f"Valor investido em R$ na época: R$ {valor_investido_reais:.2f}")
    print(f"Valor atual em R$: R$ {valor_hoje_reais:.2f}")
    print(f"Lucro: R$ {lucro:.2f} ({percentual:.2f}%)")

def simular_investimento_reais():
    try:
        valor_em_reais = float(input('Quanto você teria investido em reais? '))
        data = input("Digite a data da compra do dólar (dd/mm/aaaa): ")
    except ValueError:
        print("Valor investido inválido.")
        return

    cotacao_antiga = obter_cotacao_antiga(data)
    if cotacao_antiga is None:
        print("Não foi possível encontrar a cotação para essa data ou para os 7 dias anteriores.")
        return

    cotacao_atual = obter_cotacao_atual()
    if cotacao_atual is None:
        print("Não foi possível obter a cotação atual.")
        return

    quantidade_em_dolar = valor_em_reais / cotacao_antiga
    valor_hoje = quantidade_em_dolar * cotacao_atual
    lucro = valor_hoje - valor_em_reais
    percentual = (lucro / valor_em_reais) * 100

    print(f"\nCotação em {data}: R$ {cotacao_antiga:.2f}")
    print(f"Cotação atual: R$ {cotacao_atual:.2f}")
    print(f"Você teria hoje: R$ {valor_hoje:.2f}")
    print(f"Lucro: R$ {lucro:.2f} ({percentual:.2f}%)")

if __name__ == "__main__":
    print("Escolha a simulação:")
    print("1 - Investimento em dólar (você informa USD)")
    print("2 - Investimento em reais (você informa BRL)")
    escolha = input("Opção (1 ou 2): ").strip()
    if escolha == "1":
        simular_investimento_dolar()
    elif escolha == "2":
        simular_investimento_reais()
    else:
        print("Opção inválida.")
