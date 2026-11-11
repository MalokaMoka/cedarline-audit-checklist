"""Cybersecurity Audit Checklist — Cedarline Health Group (BINF 711 project).

Run locally:  streamlit run app.py
Data:         checklist.xlsx (the Excel export of the team's sheet). Replace that file to update content.
"""
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from core import (RESOLVED, STATUSES, bullets, load_checklist, prioritized, priority,
                  source_links)

DATA_FILE = Path(__file__).parent / "checklist.xlsx"

st.set_page_config(page_title="Cedarline Health Group: Cybersecurity Audit", page_icon="🏥", layout="wide")

RISK_COLOR = {"High": "red", "Medium": "orange", "Low": "green"}
STATUS_ICON = {"Open": "🟠", "Partially met": "🟡", "Completed": "✅", "N/A": "⚪"}


@st.cache_data
def _load(path_or_bytes, name: str) -> pd.DataFrame:
    return load_checklist(path_or_bytes)


# ---------------- data ----------------
with st.sidebar:
    st.header("🏥 Cedarline Health Group")
    st.caption("Fictional client · 3 hospitals, 14 clinics, ~4,200 workforce members · HIPAA covered entity")
    uploaded = st.file_uploader("Load an updated checklist (.xlsx)", type=["xlsx"],
                                help="Optional. By default the app uses checklist.xlsx from the repository.")

if uploaded is not None:
    tmp = Path(tempfile.gettempdir()) / "_uploaded_checklist.xlsx"
    tmp.write_bytes(uploaded.getvalue())
    df = _load(str(tmp), uploaded.name + str(uploaded.size))
else:
    df = _load(str(DATA_FILE), "default")

# Live status and notes for this session (start from the values in the file).
for _, r in df.iterrows():
    st.session_state.setdefault(f"status_{r['ID']}", r["Status"])
    st.session_state.setdefault(f"notes_{r['ID']}", r["Audit Notes / Findings"])

live = df.copy()
live["Status"] = [st.session_state[f"status_{i}"] for i in live["ID"]]
live["Audit Notes / Findings"] = [st.session_state[f"notes_{i}"] for i in live["ID"]]
live["Priority Score"] = [priority(r, u, s) for r, u, s in
                          zip(live["Risk"], live["Urgency"], live["Patient Safety Impact"])]

# ---------------- sidebar: progress + filters ----------------
with st.sidebar:
    total = len(live)
    done = int(live["Status"].isin(RESOLVED).sum())
    st.progress(done / total if total else 0.0, text=f"{done} of {total} items resolved")
    c1, c2 = st.columns(2)
    c1.metric("Open", int((live["Status"] == "Open").sum()))
    c2.metric("Partially met", int((live["Status"] == "Partially met").sum()))
    st.metric("Unresolved high-risk", int(((live["Risk"] == "High") & ~live["Status"].isin(RESOLVED)).sum()))
    st.divider()
    st.subheader("Filters")
    f_domain = st.multiselect("Domain", list(dict.fromkeys(live["Domain"])))
    f_owner = st.multiselect("Owner", sorted(live["Owner"].unique()))
    f_risk = st.multiselect("Risk", ["High", "Medium", "Low"])
    f_status = st.multiselect("Status", STATUSES)

view = live
if f_domain:
    view = view[view["Domain"].isin(f_domain)]
if f_owner:
    view = view[view["Owner"].isin(f_owner)]
if f_risk:
    view = view[view["Risk"].isin(f_risk)]
if f_status:
    view = view[view["Status"].isin(f_status)]

# ---------------- header ----------------
st.title("Cybersecurity Audit Checklist")
st.markdown("**Client:** Cedarline Health Group (fictional) · **Standards:** HIPAA Security Rule & Breach "
            "Notification Rule (45 CFR Part 164), NIST CSF 2.0, NIST SP 800-66r2, HHS HPH CPGs · "
            "**Prepared by:** BINF 711 consulting team, Winter 2026")

tab_check, tab_prio, tab_about = st.tabs(["📋 Checklist", "🚩 Prioritized Open Items", "ℹ️ About & Sources"])

# ---------------- checklist ----------------
with tab_check:
    if view.empty:
        st.info("No items match the filters.")
    for domain, items in view.groupby("Domain", sort=False):
        resolved_here = int(items["Status"].isin(RESOLVED).sum())
        st.subheader(f"{domain}  ·  {resolved_here}/{len(items)} resolved")
        for _, r in items.iterrows():
            iid = r["ID"]
            status = st.session_state[f"status_{iid}"]
            risk_tag = f":{RISK_COLOR.get(r['Risk'], 'gray')}[**{r['Risk']}**]"
            title = f"{STATUS_ICON.get(status, '')} **{iid}** · {r['TL;DR']}"
            with st.expander(title):
                st.markdown(f"#### ❓ {r['Audit Question']}")
                if r["Follow-up Probe"]:
                    st.markdown(f"**Follow-up probe:** _{r['Follow-up Probe']}_")
                m1, m2, m3, m4 = st.columns(4)
                m1.markdown(f"**Risk:** {risk_tag}")
                m2.markdown(f"**Urgency:** {r['Urgency']}")
                m3.markdown(f"**Patient safety:** {r['Patient Safety Impact'] or '—'}")
                m4.markdown(f"**Priority score:** {r['Priority Score']}")

                left, right = st.columns(2)
                with left:
                    st.markdown("**Standard & Control**")
                    st.markdown("\n".join(f"- {b}" for b in bullets(r["Standard & Control"])))
                    links = source_links(r["Standard & Control"])
                    if links:
                        st.markdown("**Source text:** " + " · ".join(f"[{lbl}]({url})" for lbl, url in links))
                    st.markdown(f"**Interview target:** {r['Interview Target'] or '—'}")
                    st.markdown(f"**Owner (our team):** {r['Owner']}")
                with right:
                    st.markdown("**Associated Action Items**")
                    st.markdown("\n".join(f"- {b}" for b in bullets(r["Associated Action Items"])))
                    if r["Evidence to Request"]:
                        st.markdown(f"**Evidence to request:** {r['Evidence to Request']}")
                st.markdown(f"**Justification:** {r['Justification']}")

                s1, s2 = st.columns([1, 3])
                s1.selectbox("Status", STATUSES, key=f"status_{iid}")
                s2.text_area("Audit notes / findings", key=f"notes_{iid}", height=80,
                             placeholder="What did the client say or show?")

# ---------------- prioritized ----------------
with tab_prio:
    roadmap = prioritized(live)
    st.markdown("Every item **not** marked Completed or N/A, ranked by **Priority Score = Risk × Urgency "
                "(+1 if the gap could affect patient safety)**. This is the remediation roadmap "
                "handed to the client at the end of the session.")
    if roadmap.empty:
        st.success("All items are resolved.")
    else:
        st.dataframe(roadmap, hide_index=True, use_container_width=True,
                     column_config={"Associated Action Items": st.column_config.TextColumn(width="large"),
                                    "TL;DR": st.column_config.TextColumn(width="medium")})
        st.download_button("⬇️ Download roadmap (CSV)", roadmap.to_csv(index=False).encode("utf-8-sig"),
                           file_name="cedarline_prioritized_open_items.csv", mime="text/csv")
    st.download_button("⬇️ Download full checklist with today's statuses (CSV)",
                       live.to_csv(index=False).encode("utf-8-sig"),
                       file_name="cedarline_checklist_session.csv", mime="text/csv")

# ---------------- about ----------------
with tab_about:
    st.markdown("""
### Client scenario (fictional)
Cedarline Health Group runs 3 hospitals and 14 outpatient clinics in the US (a HIPAA covered entity), with about
4,200 workforce members. Key facts that shape this audit: one shared EHR; cloud-hosted PACS imaging; a telehealth
service; a cardiac remote patient-monitoring program with devices in patients' homes; an outsourced IT help desk;
and 8 Brookfield clinics acquired last year that still run on separate IT.

### Scoring
| Field | Values |
|---|---|
| Risk / Severity | High = 3, Medium = 2, Low = 1 |
| Urgency | Immediate = 4, 1–2 Weeks = 3, 1–3 Months = 2, 3–6 Months = 1 |
| Patient Safety Impact | Yes adds +1 |
| **Priority Score** | Risk × Urgency (+1), maximum 13 |

**Status values:** Open = gap confirmed · Partially met = some evidence, gaps remain · Completed = client showed
evidence and we agree it is met · N/A = does not apply.

### Standards used
- **HIPAA Security Rule**: 45 CFR Part 164, Subpart C (§§164.302–164.318), the rule currently in force. [eCFR](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C)
- **HIPAA Breach Notification Rule**: 45 CFR Part 164, Subpart D (§§164.400–164.414). [eCFR](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-D)
- **NIST Cybersecurity Framework 2.0**: NIST CSWP 29 (Feb 2024); subcategory IDs are in Appendix A. [PDF](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf)
- **NIST SP 800-66 Rev. 2**: Implementing the HIPAA Security Rule (Feb 2024); Section 5 key activities, Appendix D crosswalk. [PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-66r2.pdf)
- **HHS HPH Cybersecurity Performance Goals**: 10 Essential + 10 Enhanced voluntary goals (Jan 2024). [HHS](https://hhscyber.hhs.gov/cybersecurity-performance-goals.html)
- **HHS HC3 Sector Alert**: Social Engineering Attacks Targeting IT Help Desks in the Health Sector (Apr 2024). [PDF](https://www.hhs.gov/sites/default/files/help-desk-social-engineering-sector-alert-tlpclear.pdf)

**Required vs. Addressable:** under §164.306(d)(3) an Addressable specification must be implemented if reasonable
and appropriate; otherwise the entity documents why and implements an equivalent alternative if reasonable and appropriate.

**Proposed HIPAA update:** HHS proposed a major Security Rule update on Jan 6, 2025. It is not final, so this
checklist cites the rule currently in force.
""")
    st.caption("Statuses and notes entered here last for this browser session. Use the download buttons to keep them.")
