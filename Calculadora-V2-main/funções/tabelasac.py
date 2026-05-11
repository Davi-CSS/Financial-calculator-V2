from typing import List, Dict

# GitHub Copilot
# Path: /c:/Users/Pichau/OneDrive/Documentos/calculadora/funções/tabelasac.py
# Simple interactive prompt to compute and answer questions about a SAC (Sistema de Amortização Constante) table.



def generate_sac_schedule(principal: float, rate_per_period: float, periods: int) -> List[Dict]:
    """
    Generate SAC amortization schedule.
    rate_per_period should be a decimal (e.g., 0.01 for 1% per period).
    Returns a list of dicts with keys: period, beginning_balance, amortization, interest, payment, ending_balance.
    """
    schedule = []
    amortization = principal / periods
    balance = principal
    for p in range(1, periods + 1):
        interest = balance * rate_per_period
        payment = amortization + interest
        ending_balance = balance - amortization
        schedule.append({
            "period": p,
            "beginning_balance": round(balance, 10),
            "amortization": round(amortization, 10),
            "interest": round(interest, 10),
            "payment": round(payment, 10),
            "ending_balance": round(ending_balance, 10),
        })
        balance = ending_balance
    return schedule


def format_money(x: float) -> str:
    return f"{x:,.2f}"


def print_table(schedule: List[Dict], max_rows: int = None) -> None:
    rows = schedule if max_rows is None else schedule[:max_rows]
    header = f"{'P':>3} {'Begin':>15} {'Amort':>12} {'Interest':>12} {'Payment':>12} {'End':>15}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['period']:>3} {format_money(r['beginning_balance']):>15} {format_money(r['amortization']):>12} "
              f"{format_money(r['interest']):>12} {format_money(r['payment']):>12} {format_money(r['ending_balance']):>15}")


def total_interest(schedule: List[Dict]) -> float:
    return sum(r["interest"] for r in schedule)


def total_paid(schedule: List[Dict]) -> float:
    return sum(r["payment"] for r in schedule)


def cli():
    print("SAC Table helper")
    try:
        principal = float(input("Principal (e.g. 100000.00): ").strip())
        rate_input = float(input("Rate (numeric). If annual, append 'a' (e.g. 12a) else monthly (e.g. 1): ").strip().rstrip().lower())
    except ValueError:
        # allow input like "12a" parsed above would have thrown; try raw string path
        raw = str(rate_input)
    # Re-ask rate properly to support 'a' suffix.
    while True:
        raw_rate = input("Rate (e.g. 1 for 1% per period OR 12a for 12% per year): ").strip().lower()
        if raw_rate.endswith('a'):
            try:
                annual = float(raw_rate[:-1])
                rate_per_period = annual / 100.0 / 12.0
                print(f"Assuming monthly periods. Using rate_per_period = {rate_per_period:.6f} (annual {annual}%)")
                break
            except ValueError:
                print("Invalid rate. Try again.")
        else:
            try:
                r = float(raw_rate)
                rate_per_period = r / 100.0
                break
            except ValueError:
                print("Invalid rate. Try again.")
    while True:
        try:
            periods = int(input("Number of periods (integer): ").strip())
            if periods <= 0:
                raise ValueError
            break
        except ValueError:
            print("Enter a positive integer for periods.")
    schedule = generate_sac_schedule(principal, rate_per_period, periods)
    print("Schedule generated. Commands: 'show', 'show n', 'remaining n', 'interest total', 'paid total', 'help', 'exit'")

    while True:
        cmd = input(">> ").strip().lower()
        if cmd in ("exit", "quit"):
            print("Bye.")
            break
        if cmd in ("help", "?"):
            print("Commands:")
            print("  show            - print full table")
            print("  show n          - print first n rows (e.g. 'show 6')")
            print("  remaining n     - show remaining balance after period n (ending balance of period n)")
            print("  interest total  - total interest paid over all periods")
            print("  paid total      - total paid (principal + interest) over all periods")
            print("  payment n       - show payment, interest, amortization for period n")
            print("  exit            - quit")
            continue
        if cmd.startswith("show"):
            parts = cmd.split()
            if len(parts) == 1:
                print_table(schedule)
            else:
                try:
                    n = int(parts[1])
                    print_table(schedule, max_rows=n)
                except ValueError:
                    print("Invalid number.")
            continue
        if cmd.startswith("remaining"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: remaining n")
                continue
            try:
                n = int(parts[1])
                if not 1 <= n <= len(schedule):
                    print("n out of range.")
                    continue
                eb = schedule[n - 1]["ending_balance"]
                print(f"Remaining balance after period {n}: {format_money(eb)}")
            except ValueError:
                print("Invalid number.")
            continue
        if cmd == "interest total":
            ti = total_interest(schedule)
            print(f"Total interest: {format_money(ti)}")
            continue
        if cmd == "paid total":
            tp = total_paid(schedule)
            print(f"Total paid: {format_money(tp)}")
            continue
        if cmd.startswith("payment"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: payment n")
                continue
            try:
                n = int(parts[1])
                if not 1 <= n <= len(schedule):
                    print("n out of range.")
                    continue
                r = schedule[n - 1]
                print(f"Period {n}: Payment={format_money(r['payment'])}, Interest={format_money(r['interest'])}, "
                      f"Amortization={format_money(r['amortization'])}, End={format_money(r['ending_balance'])}")
            except ValueError:
                print("Invalid number.")
            continue
        print("Unknown command. Type 'help' for list.")


if __name__ == "__main__":
    cli()