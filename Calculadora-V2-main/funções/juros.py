def calcular_juros_compostos(capital, taxa, tempo):
    montante = capital * (1 + taxa) ** tempo
    taxa = taxa * 100  # Convertendo para porcentagem
    juros = montante - capital
    return montante, juros

if __name__ == "__main__":
    print('\nDigite o capital, a taxa de juros e o tempo:')
    try:
        capital = float(input('Capital: '))
        taxa = float(input('Taxa de juros (em decimal): '))
        tempo = float(input('Tempo (em anos): '))
    except ValueError:
        print("Entrada inválida.")
        exit()

    montante, juros = calcular_juros_compostos(capital, taxa, tempo)
    print(f'O montante é: R$ {montante:.2f}')
    print(f'O juros é: R$ {juros:.2f}')

