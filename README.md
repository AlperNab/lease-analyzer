# lease-analyzer

> **Residential or commercial lease → tenant risk analysis.** Unusual clauses flagged, plain-English summary, negotiation points, missing protections, verdict: sign / negotiate / walk away.

[![PyPI](https://img.shields.io/pypi/v/lease-analyzer?style=flat)](https://pypi.org/project/lease-analyzer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Quickstart

```bash
pip install lease-analyzer
python -m lease_analyzer lease.pdf
python -m lease_analyzer apartment_contract.txt --json
```

## What it extracts

- Rent, deposit, grace period, late fees, escalation clauses
- Entry rights (notice required, emergency access)
- Subletting, pets, alterations policies
- Early termination penalties and notice requirements
- Auto-renewal traps with notice-to-cancel deadlines
- Every issue scored critical → low with tenant impact
- Missing protections you should push for
- Suggested negotiation language per clause

## Works on

PDF and plain text. Residential apartments, commercial offices, retail leases, 
warehouse agreements — any lease type in any jurisdiction.

## License
MIT © [Alper Nabil Gabra Zakher](https://github.com/AlperNab)
