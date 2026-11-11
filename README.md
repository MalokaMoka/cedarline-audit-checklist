# Cybersecurity Audit Checklist: Cedarline Health Group

BINF 711 (Winter 2026) course project. An interactive audit checklist for a fictional US hospital group,
built on the HIPAA Security Rule and Breach Notification Rule (45 CFR Part 164), NIST CSF 2.0,
NIST SP 800-66 Rev. 2 and the HHS HPH Cybersecurity Performance Goals.

**Live app:** _paste your Streamlit link here after deploying_

## What's in the app
- **Checklist:** 44 items in 7 functional domains. Each item has an audit question, standard & control,
  action items, risk, urgency, justification, interview target, evidence to request, a follow-up probe,
  and links to the official source text. Mark each item's status and take notes live during the session.
- **Prioritized Open Items:** unresolved items ranked by Priority Score = Risk × Urgency (+1 if patient
  safety is affected). Downloadable as CSV for the client.
- **About & Sources:** client scenario, scoring method and the standards used.

## Files
| File | Purpose |
|---|---|
| `app.py` | The Streamlit app |
| `core.py` | Data loading, scoring and source links |
| `checklist.xlsx` | The checklist content. **To update content, replace this file** with a new Excel export of the sheet (keep the sheet name `Checklist` and the header row) |
| `requirements.txt` | Python packages |

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Team
| Member | Items |
|---|---|
| Member 1 | GOV-01 to GOV-08, VEN-01 to VEN-03 |
| Member 2 | IAM-01 to IAM-09, VEN-04, VEN-05 |
| Member 3 | NET-01 to NET-06, AVM-01 to AVM-05 |
| Member 4 | DAT-01 to DAT-05, IR-01 to IR-06 |
