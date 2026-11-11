"""Data logic for the audit checklist app (no Streamlit imports, so it can be tested on its own)."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ECFR = "https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164"
SOURCE_URLS = {
    "NIST CSF 2.0 (Appendix A)": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
    "NIST SP 800-66r2": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-66r2.pdf",
    "HHS HPH Cybersecurity Performance Goals": "https://hhscyber.hhs.gov/cybersecurity-performance-goals.html",
    "HHS HC3 Help-Desk Sector Alert": "https://www.hhs.gov/sites/default/files/help-desk-social-engineering-sector-alert-tlpclear.pdf",
}

RISK_POINTS = {"High": 3, "Medium": 2, "Low": 1}
URGENCY_POINTS = {"Immediate": 4, "1–2 Weeks": 3, "1–3 Months": 2, "3–6 Months": 1}
STATUSES = ["Open", "Partially met", "Completed", "N/A"]
RESOLVED = {"Completed", "N/A"}

# Column names exactly as they appear in the "Checklist" sheet header row.
REQUIRED = ["ID", "Domain", "Status", "TL;DR", "Audit Question", "Risk", "Urgency",
            "Standard & Control", "Associated Action Items", "Justification", "Owner"]
OPTIONAL = ["Interview Target", "Evidence to Request", "Follow-up Probe",
            "Patient Safety Impact", "Audit Notes / Findings"]


def _norm_dash(s: str) -> str:
    """Accept '1-2 Weeks' typed with a plain hyphen as well as the en dash."""
    return re.sub(r"(\d)\s*[-–]\s*(\d)", r"\1–\2", s.strip())


def priority(risk: str, urgency: str, safety: str) -> int:
    return (RISK_POINTS.get(str(risk).strip(), 0) * URGENCY_POINTS.get(_norm_dash(str(urgency)), 0)
            + (1 if str(safety).strip().lower() == "yes" else 0))


def ecfr_url(section: str) -> str:
    """section like '164.312' -> eCFR URL in the right subpart."""
    n = int(section.split(".")[1])
    sub = "C" if 302 <= n <= 318 else "D" if 400 <= n <= 414 else "E" if 500 <= n <= 534 else None
    if sub is None:
        return f"https://www.ecfr.gov/current/title-45/section-{section}"
    return f"{ECFR}/subpart-{sub}/section-{section}"


def source_links(standards_text: str) -> list[tuple[str, str]]:
    """Build (label, url) links from the citations written in 'Standard & Control'."""
    text = str(standards_text)
    links: list[tuple[str, str]] = []
    seen = set()
    for sec in re.findall(r"§\s?(164\.\d{3})", text):
        if sec not in seen:
            seen.add(sec)
            links.append((f"45 CFR §{sec} (eCFR)", ecfr_url(sec)))
    checks = [("NIST CSF", "NIST CSF 2.0 (Appendix A)"), ("800-66", "NIST SP 800-66r2"),
              ("HPH CPG", "HHS HPH Cybersecurity Performance Goals"), ("HC3", "HHS HC3 Help-Desk Sector Alert")]
    for needle, label in checks:
        if needle in text:
            links.append((label, SOURCE_URLS[label]))
    return links


def bullets(text) -> list[str]:
    if pd.isna(text):
        return []
    return [ln.strip().lstrip("•-* ").strip() for ln in str(text).splitlines() if ln.strip()]


def load_checklist(path: str | Path) -> pd.DataFrame:
    """Read the Excel (or CSV) export of the sheet and return a clean DataFrame."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        sheet = "Checklist" if "Checklist" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in the checklist file: {missing}")
    for c in OPTIONAL:
        if c not in df.columns:
            df[c] = ""
    df = df[df["ID"].notna() & (df["ID"].astype(str).str.strip() != "")].copy()
    for c in REQUIRED + OPTIONAL:
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["Urgency"] = df["Urgency"].map(_norm_dash)
    df["Status"] = df["Status"].where(df["Status"].isin(STATUSES), "Open")
    df["Priority Score"] = [priority(r, u, s) for r, u, s in
                            zip(df["Risk"], df["Urgency"], df["Patient Safety Impact"])]
    return df.reset_index(drop=True)


def prioritized(df: pd.DataFrame) -> pd.DataFrame:
    """Unresolved items, highest priority first (ties keep checklist order)."""
    open_items = df[~df["Status"].isin(RESOLVED)].copy()
    open_items["_order"] = range(len(open_items))
    open_items = open_items.sort_values(["Priority Score", "_order"], ascending=[False, True])
    open_items.insert(0, "Rank", range(1, len(open_items) + 1))
    cols = ["Rank", "ID", "Domain", "TL;DR", "Risk", "Urgency", "Patient Safety Impact",
            "Priority Score", "Owner", "Status", "Associated Action Items", "Audit Notes / Findings"]
    return open_items[cols]
