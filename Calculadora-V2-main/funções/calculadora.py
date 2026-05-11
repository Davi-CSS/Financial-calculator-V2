def calcular_soma(a, b):
    return a + b

def calcular_subtracao(a, b):
    return a - b

def calcular_multiplicacao(a, b):
    return a * b

def calcular_divisao(a, b):
    if b == 0:
        return 'Divisão por zero não é permitida.'
    return a / b

if __name__ == "__main__":
    print('Digite dois números:')
    try:
        num1 = float(input('Número 1: '))
        num2 = float(input('Número 2: '))
    except ValueError:
        print("Entrada inválida.")
        exit()

    print(f'A soma é: {calcular_soma(num1, num2)}')
    print(f'A subtração é: {calcular_subtracao(num1, num2)}')
    print(f'A multiplicação é: {calcular_multiplicacao(num1, num2)}')
    print(f'A divisão é: {calcular_divisao(num1, num2)}')

