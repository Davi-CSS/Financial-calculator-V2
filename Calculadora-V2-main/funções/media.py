def calcular_media():
    if __name__ == "__main__":
        print('\nDigite as notas para calcular a média:')
        notas = []
        for i in range(1, 5):
            try:
                nota = float(input(f'Nota {i}: '))
                notas.append(nota)
            except ValueError:
                print("Entrada inválida.")
                exit()

        media = sum(notas) / len(notas)
        print(f'A média é: {media:.2f}')