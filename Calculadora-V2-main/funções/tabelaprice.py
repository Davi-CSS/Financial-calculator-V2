def tabela_price(capital, taxa_mensal, num_parcelas):
    """
    Calcula a Tabela Price (Sistema de Amortização Francês)
    
    Args:
        capital: Valor do empréstimo
        taxa_mensal: Taxa de juros mensal (em decimal, ex: 0.05 para 5%)
        num_parcelas: Número de parcelas
    
    Returns:
        Lista com dados de cada parcela
    """
    parcelas = []
    saldo_devedor = capital
    
    # Calcula a prestação fixa
    prestacao = capital * (taxa_mensal * (1 + taxa_mensal) ** num_parcelas) / \
                ((1 + taxa_mensal) ** num_parcelas - 1)
    
    for i in range(1, num_parcelas + 1):
        juros = saldo_devedor * taxa_mensal
        amortizacao = prestacao - juros
        saldo_devedor -= amortizacao
        
        parcelas.append({
            'parcela': i,
            'prestacao': round(prestacao, 2),
            'juros': round(juros, 2),
            'amortizacao': round(amortizacao, 2),
            'saldo_devedor': round(max(0, saldo_devedor), 2)
        })
    
    return parcelas


if __name__ == "__main__":
    capital = float(input("Valor do empréstimo: R$ "))
    taxa = float(input("Taxa de juros mensal (%): ")) / 100
    parcelas = int(input("Número de parcelas: "))
    
    resultado = tabela_price(capital, taxa, parcelas)
    
    print("\n{:<8} {:<15} {:<15} {:<15} {:<15}".format(
        "Parcela", "Prestação", "Juros", "Amortização", "Saldo Devedor"))
    print("-" * 60)
    
    for linha in resultado:
        print("{:<8} R${:<14.2f} R${:<14.2f} R${:<14.2f} R${:<14.2f}".format(
            linha['parcela'], linha['prestacao'], linha['juros'],
            linha['amortizacao'], linha['saldo_devedor']))