import streamlit as st
import numpy as np
import plotly.graph_objs as go
import streamlit.components.v1 as components
import re, csv, os, datetime

# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FLOKA • Analytics Readiness Diagnostic",
    page_icon="floka_logo.png",
    layout="wide"
)

# -----------------------------------------------------------------------------
# GLOBAL HELPERS
# -----------------------------------------------------------------------------
def is_admin() -> bool:
    """Show internal-only controls when URL has ?key=<ADMIN_KEY> matching secrets/env."""
    key_in_url = ""
    try:
        qp = st.query_params
        key_in_url = qp.get("key", [""])[0] if isinstance(qp.get("key"), list) else qp.get("key", "")
    except Exception:
        qp = st.experimental_get_query_params()
        key_in_url = qp.get("key", [""])[0] if qp.get("key") else ""
    expected = st.secrets.get("ADMIN_KEY", os.environ.get("ADMIN_KEY", ""))
    return (expected != "") and (key_in_url == expected)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^[0-9+()\-\s]{7,}$")
CSV_PATH = "responses.csv"

def valid_email(s: str) -> bool:
    return bool(EMAIL_RE.match((s or "").strip()))

def valid_phone(s: str) -> bool:
    return bool(PHONE_RE.match((s or "").strip()))

def append_to_csv(row: list, path=CSV_PATH):
    header = [
        "timestamp_utc","email","mobile",
        "overall","level",
        "people","process","platform","performance",
        "bottleneck"
    ]
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(header)
        w.writerow(row)

# -----------------------------------------------------------------------------
# THEME & CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
:root {
  --floka-blue:#1552FF;
  --floka-navy:#0A1024;
  --bg:#FFFFFF;
  --card:#F5F7FF;
}
html, body, [class*="css"]  {
  color:#0A1024;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif;
}
section.main > div { padding-top: 10px !important; }

/* Primary button */
.stButton>button {
  background:#1552FF !important;
  color:#FFFFFF !important;
  border:1px solid #1552FF !important;
  border-radius:10px !important;
  padding:.7rem 1.1rem !important;
  font-weight:600 !important;
}
.stButton>button:hover { filter:brightness(0.95); }

/* Info cards */
.floka-card {
  background: var(--card);
  border: 1px solid rgba(21,82,255,.12);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.header-wrap {display:flex;align-items:center;gap:14px;margin-bottom:6px;}
.badge {display:inline-block;background:#E7EEFF;color:#1552FF;border:1px solid #cfe0ff;padding:2px 8px;border-radius:999px;font-size:12px;margin-left:6px;}
.footer {text-align:center;color:#6B7280;margin:30px 0 6px;}
hr{border-color:#eef2ff;}

.tagline{
  font-size: 22px;
  font-weight: 600;
  color: #0A1024;
  opacity: .9;
  margin: -2px 0 12px 0;
}

/* Sticky nav */
#floka-nav {
  position: sticky; top: 0; z-index: 1000;
  background: #FFFFFF; border-bottom: 1px solid #e6ecff;
  padding: 10px 4px; margin: -8px -8px 12px -8px;
}
#floka-nav .floka-wrap {max-width: 1200px; margin: 0 auto; display:flex; gap:10px; flex-wrap:wrap;}

/* Solid blue pills for ALL tabs */
#floka-nav .link {
  cursor:pointer; padding:6px 12px; border-radius:888px;
  text-decoration:none; background:#1552FF; color:#FFFFFF !important;
  border:1px solid #1552FF; transition: filter .15s ease, transform .02s ease;
}
#floka-nav .link:hover, #floka-nav .link:focus { filter:brightness(0.95); }
#floka-nav .link.active { box-shadow: 0 0 0 3px rgba(21,82,255,.18); }

/* Maturity table styles (blue header, no-wrap Range) */
.level-card { background:#F5F7FF; border:1px solid #e6ecff; border-radius:14px; padding:14px; }
.level-table { width:100%; border-collapse:separate; border-spacing:0; border:1px solid #e6ecff; border-radius:10px; overflow:hidden; }
.level-table thead th { background:#1552FF; color:#FFFFFF; text-align:left; }
.level-table th, .level-table td { padding:10px 12px; border-bottom:1px solid #eef2ff; vertical-align:top; }
.level-table tr:last-child td { border-bottom:0; }
.level-table .range-col { white-space:nowrap; width:130px; }
.level-table .level-col { width:140px; }

/* Likert radios: inline layout */
[data-testid="stRadio"] > label { font-weight: 500; }
[data-testid="stRadio"] > div { flex-wrap: wrap; gap: .6rem 1rem; }
@media (min-width: 900px){
  [data-testid="stRadio"] > div { flex-wrap: nowrap; }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# LOGO + TITLE
# -----------------------------------------------------------------------------
col_logo, col_title = st.columns([1,5], vertical_alignment="center")
with col_logo:
    st.image("floka_logo.png", width=120)
with col_title:
    st.markdown(
        "<div class='header-wrap'><h1>Analytics Readiness Diagnostic</h1>"
        "<span class='badge'>People • Process • Platform • Performance</span></div>",
        unsafe_allow_html=True
    )
    st.markdown("<div class='tagline'>How ready is your business to extract value from analytics?</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# STICKY NAV (click to jump + active on scroll)
# -----------------------------------------------------------------------------
st.markdown("""
<div id="floka-nav">
  <div class="floka-wrap">
    <a class="link active" data-target="people">People &amp; Leadership</a>
    <a class="link" data-target="process">Process &amp; Governance</a>
    <a class="link" data-target="platform">Platform &amp; Technology</a>
    <a class="link" data-target="performance">Performance &amp; Value</a>
    <a class="link" data-target="results">See Results</a>
  </div>
</div>
""", unsafe_allow_html=True)

components.html("""
<script>
(function(){
  const nav = parent.document.querySelector('#floka-nav');
  if(nav){
    function scrollToId(id){
      const el = parent.document.getElementById(id);
      if(el){ el.scrollIntoView({behavior:'smooth', block:'start'}); }
    }
    nav.querySelectorAll('.link').forEach(a=>{
      a.addEventListener('click', e=>{
        e.preventDefault();
        scrollToId(a.dataset.target);
      });
    });
    const ids = ['people','process','platform','performance','results'];
    const observer = new IntersectionObserver((entries)=>{
      entries.forEach((en)=>{
        if(en.isIntersecting){
          nav.querySelectorAll('.link').forEach(x=>x.classList.remove('active'));
          const active = nav.querySelector(`.link[data-target="${en.target.id}"]`);
          if(active) active.classList.add('active');
        }
      });
    },{ root: parent.document, rootMargin: '-25% 0px -65% 0px', threshold: [0, 0.01] });
    ids.forEach(id=>{
      const el = parent.document.getElementById(id);
      if(el) observer.observe(el);
    });
  }
})();
</script>
""", height=0)

st.markdown(
    f"""
<div class='floka-card'><b>How it works</b><br>
Rate each statement from <b>1 (Strongly Disagree)</b> to <b>5 (Strongly Agree)</b>.
You will instantly see your maturity level, a radar chart by pillar, and tailored recommendations.
<br><br><b>Rating guide</b>
{RATING_GUIDE}
</div>
""",
    unsafe_allow_html=True
)


# -----------------------------------------------------------------------------
# QUESTIONS
# -----------------------------------------------------------------------------
questions = [
    # People & Leadership
    ("People & Leadership", "Leadership shares a clear vision for how analytics creates business value."),
    ("People & Leadership", "Decision-makers trust data and use it to challenge assumptions."),
    ("People & Leadership", "Teams across functions have the skills and tools to analyze and interpret data independently."),
    # Process & Governance
    ("Process & Governance", "Analytics initiatives are prioritized based on measurable business outcomes."),
    ("Process & Governance", "Data governance, standards, and accountabilities are defined and adopted."),
    ("Process & Governance", "We learn from pilots and reliably scale what works across the business."),
    # Platform & Technology
    ("Platform & Technology", "Data is integrated and accessible through a governed single source of truth."),
    ("Platform & Technology", "Data flows and reporting processes are automated and scalable."),
    ("Platform & Technology", "Security, privacy, and regulatory requirements are consistently met."),
    # Performance & Value
    ("Performance & Value", "We can quantify the business impact of analytics (savings, revenue, efficiency)."),
    ("Performance & Value", "Business users consistently act on insights, not just view dashboards."),
    ("Performance & Value", "We track and refine models, metrics, and dashboards to keep them relevant.")
]

# Pillar definition cards (right column)
DEFINITIONS = {
    "People & Leadership": (
        "<div class='floka-card'><b>What this pillar covers</b><br>"
        "Vision and sponsorship, culture and behaviors, and the capability to work with data across functions. "
        "Leaders make value explicit and set the rhythm for evidence-based decisions.</div>"
    ),
    "Process & Governance": (
        "<div class='floka-card'><b>What this pillar covers</b><br>"
        "How ideas become outcomes: prioritization, standards, ownership, risk & compliance, and a scale/learn rhythm. "
        "Clear processes reduce rework and increase the hit-rate of analytics initiatives.</div>"
    ),
    "Platform & Technology": (
        "<div class='floka-card'><b>What this pillar covers</b><br>"
        "The data foundation: integration, automation, security and reliability. "
        "A governed source of truth and basic engineering practices enable speed with trust.</div>"
    ),
    "Performance & Value": (
        "<div class='floka-card'><b>What this pillar covers</b><br>"
        "Adoption, measurable business impact, and continuous improvement. "
        "Track who acts on insights, the results achieved, and retire or refine what is not used.</div>"
    ),
}

# Reusable rating legend (right column)
RATING_GUIDE = """
<div class='floka-card'>
  <b>Rating guide</b>
  <ul style="margin:6px 0 0 18px;">
    <li><b>1 — Strongly Disagree:</b> practice largely absent or ad hoc</li>
    <li><b>2 — Disagree:</b> some activity but inconsistent and fragile</li>
    <li><b>3 — Neutral:</b> partially in place; varies by team</li>
    <li><b>4 — Agree:</b> established and repeatable in most areas</li>
    <li><b>5 — Strongly Agree:</b> optimized, measured, and continuously improved</li>
  </ul>
</div>
"""

# -----------------------------------------------------------------------------
# FORM (two-column sections; Likert radios on the left)
# -----------------------------------------------------------------------------
likert_options = [
    "1 - Strongly Disagree",
    "2 - Disagree",
    "3 - Neutral",
    "4 - Agree",
    "5 - Strongly Agree"
]

def render_section(section_id: str, title: str, idx_range: range, key_prefix: str) -> list:
    """Render a section with questions on the left and definition + rating guide on the right."""
    st.markdown(f"<div id='{section_id}'></div>", unsafe_allow_html=True)
    left, right = st.columns([7,5], vertical_alignment="top")

    answers = []
    with left:
        st.subheader(f"🔹 {title}")
        for i in idx_range:
            choice = st.radio(
                questions[i][1],
                options=likert_options,
                key=f"{key_prefix}_{i}",
                horizontal=True
            )
            answers.append(int(choice.split(" - ")[0]))

    with right:
        st.markdown(DEFINITIONS[title], unsafe_allow_html=True)
       

    return answers

with st.form("quiz"):
    scores = []
    # Sections
    scores += render_section("people", "People & Leadership", range(0, 3), "people")
    scores += render_section("process", "Process & Governance", range(3, 6), "process")
    scores += render_section("platform", "Platform & Technology", range(6, 9), "platform")
    scores += render_section("performance", "Performance & Value", range(9, 12), "performance")

    st.markdown("---")
    st.subheader("Contact (to send you a debrief)")
    left_c, right_c = st.columns(2)
    with left_c:
        email = st.text_input("Work email (required)", placeholder="name@company.com")
    with right_c:
        mobile = st.text_input("Mobile (required)", placeholder="+27 82 123 4567")

    bottleneck = st.text_input("Optional: What is your biggest analytics challenge right now?")
    st.caption("We only use your details to follow up on your results. No spam, no sharing.")

    submitted = st.form_submit_button("See My Results")

# -----------------------------------------------------------------------------
# MATURITY MODEL
# -----------------------------------------------------------------------------
LEVELS = [
    ("Emerging",      (1.00, 2.00), "Analytics efforts are ad hoc, siloed, and largely reactive. Data lives in spreadsheets."),
    ("Developing",    (2.01, 3.20), "Some structure exists, but inconsistent data and unclear ownership limit value."),
    ("Scaling",       (3.21, 4.10), "Governance and platforms are established; now the focus is on adoption and measurable impact."),
    ("Transforming",  (4.11, 5.00), "Analytics is strategic, embedded in daily decisions, and driving measurable performance gains.")
]
def maturity_label(avg: float) -> str:
    for name, (lo, hi), _ in LEVELS:
        if lo <= avg <= hi:
            return name
    return "—"
def maturity_desc(level: str) -> str:
    for name, _, desc in LEVELS:
        if name == level:
            return desc
    return ""

def levels_table_html():
    header = """
    <div class="level-card">
      <h4 style="margin:0 0 8px 0;">What do the maturity levels mean?</h4>
      <table class="level-table">
        <thead>
          <tr>
            <th class="range-col">Range</th>
            <th class="level-col">Level</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
    """
    rows = []
    for name, (lo, hi), desc in LEVELS:
        rows.append(
            f"<tr>"
            f"<td class='range-col'>{lo:.2f} – {hi:.2f}</td>"
            f"<td class='level-col'><b>{name}</b></td>"
            f"<td>{desc}</td>"
            f"</tr>"
        )
    footer = "</tbody></table></div>"
    return header + "".join(rows) + footer

# -----------------------------------------------------------------------------
# RESULTS
# -----------------------------------------------------------------------------
if submitted:
    if not valid_email(email):
        st.error("Please enter a valid work email.")
        st.stop()
    if not valid_phone(mobile):
        st.error("Please enter a valid mobile number (digits, +, spaces, () or -).")
        st.stop()

    people = np.mean(scores[0:3])
    process = np.mean(scores[3:6])
    platform = np.mean(scores[6:9])
    performance = np.mean(scores[9:12])
    overall = float(np.mean([people, process, platform, performance]))

    level = maturity_label(overall)
    desc  = maturity_desc(level)

    row = [
        datetime.datetime.utcnow().isoformat(),
        email.strip(),
        mobile.strip(),
        round(overall, 2), level,
        round(people, 2), round(process, 2), round(platform, 2), round(performance, 2),
        (bottleneck or "")
    ]
    try:
        append_to_csv(row)
        st.success("Saved. Your results are below.")
    except Exception as e:
        st.warning(f"Could not save locally ({e}). Results still shown below.")

    st.markdown("<div id='results'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## Results Summary")

    st.markdown(
        f"<div class='floka-card'><b>Maturity Level:</b> <span class='badge'>{level}</span>"
        f"<br><span>{desc}</span></div>", unsafe_allow_html=True
    )
    st.write("")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall", f"{overall:.2f}", level)
    c2.metric("People & Leadership", f"{people:.2f}")
    c3.metric("Process & Governance", f"{process:.2f}")
    c4.metric("Platform & Technology", f"{platform:.2f}")
    c5.metric("Performance & Value", f"{performance:.2f}")

    cats_full  = ["People & Leadership","Process & Governance","Platform & Technology","Performance & Value"]
    cats_short = ["People","Process","Platform","Performance"]
    values = [people, process, platform, performance]

    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r = values + [values[0]],
        theta = cats_full + [cats_full[0]],
        fill='toself',
        fillcolor="rgba(21,82,255,0.20)",
        line=dict(color="#1552FF", width=3),
        hovertemplate = "%{theta}: <b>%{r:.2f}</b><extra></extra>",
        name="Maturity"
    ))
    radar.update_layout(
        showlegend=False,
        margin=dict(l=10,r=10,t=10,b=10),
        height=420,
        polar=dict(
            radialaxis=dict(visible=True, range=[1,5], tick0=1, dtick=0.5),
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickmode="array",
                tickvals=cats_full,
                ticktext=cats_short
            )
        )
    )

    left, right = st.columns([7,5], vertical_alignment="top")
    with left:
        st.plotly_chart(radar, use_container_width=True)
    with right:
        st.markdown(levels_table_html(), unsafe_allow_html=True)

    st.markdown("### Personalized Recommendations")
    pillar_scores = {
        "People & Leadership": people,
        "Process & Governance": process,
        "Platform & Technology": platform,
        "Performance & Value": performance
    }
    weakest = min(pillar_scores, key=pillar_scores.get)
    st.markdown(f"**Primary Focus Area:** `{weakest}`")

    if weakest == "People & Leadership":
        st.write(
            "Start by making analytics value explicit in leadership routines. Draft a 12-month analytics vision that names three "
            "business outcomes (for example: throughput uplift, working-capital release, or customer NPS). Translate that vision "
            "into two or three OKRs owned by executives and publish them on the same page as financial and operational scorecards. "
            "When leaders see the analytics targets alongside P&L drivers, sponsorship and resource allocation become predictable."
        )
        st.write(
            "In parallel, lift frontline capability so teams can self-serve insight. Run a four-week data-literacy sprint focused "
            "on interpreting charts, challenging assumptions with data, and telling a short story with evidence. Pair each function "
            "with an analytics partner for one use case and close the loop in monthly ‘Decisions from Data’ sessions—review the "
            "decision, the evidence used, and the outcome. This creates a visible culture shift without heavy tooling changes."
        )

    elif weakest == "Process & Governance":
        st.write(
            "Introduce a lightweight governance rhythm that connects ideas to measurable value. Maintain a single backlog and rank "
            "items on value vs. effort; pick 1–2 initiatives per quarter with named owners, baselines, and 6–8-week targets. "
            "Formalize a stage-gate from discovery -> pilot -> scale, and require a short, written hypothesis before work starts. "
            "This stops random acts of analytics and builds organizational muscle for repeatable delivery."
        )
        st.write(
            "At the same time, make standards easy to adopt. Set up a cross-functional Data Governance Committee to own "
            "definitions, naming rules, and access policies. Publish certified metrics and code lists in a simple catalog and add a "
            "light issue log so teams can raise and resolve data problems quickly. When processes are clear, adoption and impact follow."
        )

    elif weakest == "Platform & Technology":
        st.write(
            "Stabilize the foundation by creating one governed source of truth for a core domain (e.g., customers, assets, or orders). "
            "Expose it through a semantic model so BI, analytics, and apps all reference the same logic. Automate ingest-transform-publish "
            "with basic monitoring and alerts; the goal is trustworthy, low-friction data rather than a big-bang platform rebuild."
        )
        st.write(
            "Layer in pragmatic engineering practices that accelerate delivery. Template reusable pipelines, keep transformations under "
            "version control, and enable simple CI/CD for analytics code. Add role-based access and minimum viable PII handling first, "
            "then evolve to lineage and policy checks. A small set of engineering conventions will remove most platform bottlenecks."
        )

    else:
        st.write(
            "Tie analytics work to economic outcomes and track adoption explicitly. For each initiative, agree a value formula "
            "(cost avoided, revenue generated, time saved) and a baseline; publish monthly actuals in the same place stakeholders "
            "already watch performance. Add a simple 'who acts, by when, and what happened' panel to priority dashboards so the "
            "insight-to-action chain is visible and accountable."
        )
        st.write(
            "Close the loop with continuous improvement. Run quarterly reviews of models, metrics, and dashboards—retire what is stale, "
            "refine what is used, and A/B test changes where feasible. Share short win stories that link action to outcome; over time "
            "this builds confidence, unlocks further funding, and shifts analytics from reporting to results."
        )

    if is_admin() and os.path.exists(CSV_PATH):
        with open(CSV_PATH, "rb") as f:
            st.download_button(
                label="⬇️ Download leads (CSV)",
                data=f.read(),
                file_name="floka_analytics_leads.csv",
                mime="text/csv"
            )

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("<div class='footer'>© 2025 FLOKA Solutions • Analytics Readiness Diagnostic</div>", unsafe_allow_html=True)


