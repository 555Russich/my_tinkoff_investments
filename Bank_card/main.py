import time

TARIFFS = {'USUAL': 0.05, 'PRO': 0.07}


def main(TARIFF='USUAL', SUM=105000, MONTH=6, MONTH_DEPOSIT=0):
    first_sum = SUM
    month_sum = 0
    DEP_COUNT = 0

    for i in range(1, MONTH*30+1):
        month_sum += first_sum * (TARIFFS[TARIFF] / 365)
        if i % 30 == 0:
            SUM += MONTH_DEPOSIT + month_sum
            DEP_COUNT += 1
            if TARIFF == 'PRO':
                SUM -= 199
            month_sum = 0

    print(f'''
Tariff: {TARIFF}, Percent: {round(TARIFFS[TARIFF] * 100)}%
First sum: {first_sum}
Month deposit: {MONTH_DEPOSIT}
Deposit sum: {DEP_COUNT*MONTH_DEPOSIT}
Month hold money: {MONTH}
Outcome: {round(SUM, 2)}
Profit: {round(SUM-first_sum-MONTH_DEPOSIT*DEP_COUNT, 2)}
''')


if __name__ == '__main__':
    main()