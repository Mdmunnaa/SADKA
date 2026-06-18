from django.shortcuts import render
from decimal import Decimal, InvalidOperation


# Default Nisab reference (silver standard, ~612.36g) — approximate, user should verify with current market rate
DEFAULT_SILVER_NISAB_BDT = Decimal('333736')
ZAKAT_RATE = Decimal('0.025')  # 2.5%


def zakat_calculator(request):
    result = None
    breakdown = {}

    if request.method == 'POST':
        def get_amt(key):
            val = request.POST.get(key, '').strip()
            if not val:
                return Decimal('0')
            try:
                return Decimal(val)
            except InvalidOperation:
                return Decimal('0')

        cash = get_amt('cash')
        bank_savings = get_amt('bank_savings')
        gold_value = get_amt('gold_value')
        silver_value = get_amt('silver_value')
        business_assets = get_amt('business_assets')
        investments = get_amt('investments')
        receivables = get_amt('receivables')

        debts = get_amt('debts')

        nisab_threshold = get_amt('nisab_threshold')
        if nisab_threshold <= 0:
            nisab_threshold = DEFAULT_SILVER_NISAB_BDT

        total_assets = cash + bank_savings + gold_value + silver_value + business_assets + investments + receivables
        net_zakatable = total_assets - debts
        if net_zakatable < 0:
            net_zakatable = Decimal('0')

        is_eligible = net_zakatable >= nisab_threshold
        zakat_due = (net_zakatable * ZAKAT_RATE) if is_eligible else Decimal('0')

        breakdown = {
            'cash': cash, 'bank_savings': bank_savings, 'gold_value': gold_value,
            'silver_value': silver_value, 'business_assets': business_assets,
            'investments': investments, 'receivables': receivables, 'debts': debts,
        }
        result = {
            'total_assets': total_assets,
            'net_zakatable': net_zakatable,
            'nisab_threshold': nisab_threshold,
            'is_eligible': is_eligible,
            'zakat_due': zakat_due,
        }

    context = {
        'result': result,
        'breakdown': breakdown,
        'default_nisab': DEFAULT_SILVER_NISAB_BDT,
    }
    return render(request, 'donations/zakat_calculator.html', context)
