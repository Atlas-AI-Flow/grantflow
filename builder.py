        amount = g.get('amount', 'Variable')
        if amount and str(amount).replace(',','').isdigit():
            amount = f"${amount}"
            
        tldr = (g.get('tldr') or 'Click to see details.').strip()
        if len(tldr) > 100: tldr = tldr[:97] + "..."