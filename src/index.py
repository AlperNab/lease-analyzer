#!/usr/bin/env python3
"""
lease-analyzer — residential or commercial lease → tenant risk flags,
unusual clauses, plain-English summary, negotiation points, red lines
"""
import anthropic, base64, json, re, sys
from pathlib import Path

SYSTEM = """You are a tenant-side real estate attorney who has reviewed thousands of leases.
Analyze this lease from the TENANT'S perspective.

Return ONLY valid JSON — no markdown, no explanation.

{
  "lease_type": "residential|commercial|retail|industrial",
  "property_type": "apartment|house|office|retail|warehouse|other",
  "parties": {"landlord":"string or null","tenant":"string or null"},
  "property_address": "string or null",
  "term": {"start":"YYYY-MM-DD or null","end":"YYYY-MM-DD or null","months":number_or_null},
  "rent": {
    "monthly": number_or_null,
    "currency": "USD|GBP|EGP|...",
    "due_date": "e.g. 1st of month",
    "grace_period_days": number_or_null,
    "late_fee": "string or null",
    "escalation": "string or null",
    "includes_utilities": true_or_false,
    "utilities_included": ["list or empty"]
  },
  "deposit": {
    "amount": number_or_null,
    "months_rent_equivalent": number_or_null,
    "return_timeline_days": number_or_null,
    "deduction_conditions": ["list of conditions landlord can deduct for"]
  },
  "risk_score": number_0_to_100,
  "risk_level": "low|medium|high|critical",
  "issues": [
    {
      "clause": "quoted text under 60 words",
      "issue": "what's wrong and why it matters",
      "severity": "critical|high|medium|low",
      "tenant_impact": "how this hurts you specifically",
      "negotiation_point": "how to raise this",
      "suggested_change": "proposed replacement language"
    }
  ],
  "tenant_obligations": ["list of what tenant must do"],
  "landlord_obligations": ["list of what landlord must do"],
  "prohibited_uses": ["list of things tenant cannot do"],
  "entry_rights": {
    "notice_required_hours": number_or_null,
    "emergency_entry": true_or_false,
    "inspection_frequency": "string or null"
  },
  "subletting": "allowed|not_allowed|with_permission",
  "pets": "allowed|not_allowed|with_deposit",
  "alterations": "allowed|not_allowed|with_permission|cosmetic_only",
  "early_termination": {
    "allowed": true_or_false,
    "penalty": "string or null",
    "notice_days": number_or_null
  },
  "renewal": {
    "auto_renewal": true_or_false,
    "notice_to_prevent_days": number_or_null,
    "renewal_terms": "same|renegotiated|cpi_adjusted"
  },
  "dispute_resolution": "court|arbitration|mediation",
  "governing_law": "string or null",
  "missing_tenant_protections": ["important protections NOT in this lease"],
  "green_flags": ["tenant-friendly provisions"],
  "summary": "4-5 sentence plain-English summary for the tenant",
  "verdict": "sign|negotiate|walk_away",
  "verdict_reason": "one sentence",
  "confidence": 0.0
}"""

def analyze(source: str) -> dict:
    client = anthropic.Anthropic()
    path = Path(source)
    if path.exists():
        if source.endswith(".pdf"):
            data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
            content = [
                {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":data}},
                {"type":"text","text":"Analyze this lease from the tenant's perspective."}
            ]
        else:
            text = path.read_text(encoding="utf-8",errors="replace")[:60000]
            content = [{"type":"text","text":f"Analyze this lease:\n\n{text}"}]
    else:
        content = [{"type":"text","text":f"Analyze this lease:\n\n{source[:60000]}"}]
    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=4096, system=SYSTEM,
        messages=[{"role":"user","content":content}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

RISK_ICON = {"low":"🟢","medium":"🟡","high":"🔴","critical":"💀"}
SEV_ICON = {"critical":"🚨","high":"🔴","medium":"🟠","low":"🔵"}
VERDICT_ICON = {"sign":"✅","negotiate":"🤝","walk_away":"🚫"}

def print_report(r: dict):
    rent = r.get("rent",{})
    dep = r.get("deposit",{})
    term = r.get("term",{})
    risk = r.get("risk_level","medium")
    verdict = r.get("verdict","negotiate")
    print(f"\n{'═'*60}")
    print(f"  LEASE ANALYSIS — {r.get('lease_type','?').upper()}")
    print(f"  Risk: {RISK_ICON.get(risk,'')} {r.get('risk_score',0)}/100")
    print(f"  Verdict: {VERDICT_ICON.get(verdict,'')} {verdict.upper().replace('_',' ')} — {r.get('verdict_reason','')}")
    print(f"{'═'*60}")
    print(f"\n  {r.get('summary','')}")

    if rent.get("monthly"):
        curr = rent.get("currency","")
        print(f"\n  Rent:    {curr}{rent['monthly']:,.0f}/mo due {rent.get('due_date','?')}")
        if rent.get("grace_period_days"): print(f"  Grace:   {rent['grace_period_days']} days")
        if rent.get("late_fee"): print(f"  Late fee: {rent['late_fee']}")
        if rent.get("escalation"): print(f"  Escalation: {rent['escalation']}")
    if dep.get("amount"):
        print(f"  Deposit: {rent.get('currency','')}{dep['amount']:,.0f}", end="")
        if dep.get("return_timeline_days"): print(f" (returned within {dep['return_timeline_days']} days)", end="")
        print()
    if term.get("start"): print(f"  Term:    {term.get('start','?')} → {term.get('end','?')} ({term.get('months','?')} months)")

    issues = r.get("issues",[])
    if issues:
        sorted_issues = sorted(issues, key=lambda x: ["critical","high","medium","low"].index(x.get("severity","low")))
        print(f"\n{'─'*60}\n  ISSUES ({len(issues)})")
        for i in sorted_issues:
            print(f"\n  {SEV_ICON.get(i.get('severity','medium'),'')} {i.get('issue','')}")
            print(f"     Impact: {i.get('tenant_impact','')}")
            if i.get('negotiation_point'): print(f"     Negotiate: {i['negotiation_point']}")
            if i.get('clause'): print(f"     Clause: \"{i['clause'][:80]}...\"")

    green = r.get("green_flags",[])
    if green:
        print(f"\n{'─'*60}\n  TENANT-FRIENDLY CLAUSES")
        for g in green: print(f"  ✅ {g}")

    missing = r.get("missing_tenant_protections",[])
    if missing:
        print(f"\n{'─'*60}\n  PUSH FOR THESE")
        for m in missing: print(f"  + {m}")

    print(f"\n  Subletting: {r.get('subletting','?')} | Pets: {r.get('pets','?')} | Alterations: {r.get('alterations','?')}")
    entry = r.get("entry_rights",{})
    if entry.get("notice_required_hours"): print(f"  Landlord entry notice: {entry['notice_required_hours']} hours")
    print(f"  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    if len(sys.argv)<2: print("Usage: python -m lease_analyzer <lease.txt|.pdf> [--json]"); sys.exit(0)
    src = sys.argv[1] if sys.argv[1]!="-" else sys.stdin.read()
    r = analyze(src)
    if "--json" in sys.argv: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_report(r)
