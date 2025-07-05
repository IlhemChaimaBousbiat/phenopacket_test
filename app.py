
import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
from datetime import time

# ── 🔐  Password gate ---------------------------------------------------------
APP_PASSWORD = "Goudielabsecret2025"        

def check_password():
    """Stop the app until the correct password is entered."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        pwd = st.text_input("Enter password", type="password")
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
        else:
            st.stop()

check_password()   
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Phenopacket Entry", layout="wide")

# ── dropdown choices (with "Select") ────────────────────────────────────────
dd = {
    "Ind_Sex":   ["", "Male", "Female", "Unknown sex"],
    "Ind_KSex":  ["", "XX", "XY", "XXY", "Other karyotype"],
    "Ind_Vital": ["", "Alive", "Deceased"],
    "PF_Excluded": ["", "True", "False"],
    "PF_Severity": ["", "Mild", "Moderate", "Severe"],
    "D_Status":   ["", "Ongoing", "Resolved"],
    "D_Severity": ["", "Mild", "Moderate", "Severe"],
    "M_Interp":   ["", "High", "Low", "Normal"],
    "G_Zygosity":      ["", "Heterozygous", "Homozygous"],
    "G_Pathogenicity": ["", "Benign", "Pathogenic", "Vus"],
    "G_IStatus":       ["", "Causative", "Candidate"],
    "G_Action":        ["", "Actionable", "Not actionable"],
    "Med_Type":  ["", "Procedure", "Treatment", "Radiation"],
    "P_Relation": ["", "Proband", "Sibling", "Half sibling", "Parent", "Child",
                   "Aunt", "Uncle", "Grandmother", "Grandfather",
                   "First cousin", "Second cousin", "Other"],
    "P_Affected": ["", "True", "False"],
    "P_Sex":      ["", "Male", "Female", "Unknown sex"],
    "P_Deceased": ["", "True", "False"],
}

# ── field sets per section ─────────────────────────────────────────────────
fields = {
    "PF":  ["IndividualID","PhenotypeID","Label","Excluded",
            "Onset","Severity","Evidence","Modifier"],
    "D":   ["IndividualID","DiseaseID","Label","ClinicalStatus",
            "Severity","Onset","Stage"],
    "M":   ["IndividualID","Type","Value","Unit","ReferenceRange",
            "TimeObserved","Interpretation"],
    "B":   ["SampleID","IndividualID","Description","Tissue",
            "CollectionTime","HistologicalDx"],
    "G":   ["IndividualID","VariantID","Gene","HGVS","Zygosity",
            "Pathogenicity","InterpretStatus","Actionability"],
    "Med": ["IndividualID","Type","Code","Description","Start","End",
            "Agent","Dose"],
    "P":   ["FamilyID","IndividualID","Relation","Affected","Sex",
            "Deceased","RelativeCondition"],
}

def empty_df(cols): return pd.DataFrame(columns=cols)

# ── initialise session-state storage ───────────────────────────────────────
if "store" not in st.session_state:
    st.session_state.store = {sec: empty_df(cols) for sec, cols in fields.items()}
if "row_sel" not in st.session_state:
    st.session_state.row_sel = {sec: None for sec in fields}

# ── convenience to add / delete rows ---------------------------------------
def add_row(sec, row_dict):
    st.session_state.store[sec] = pd.concat(
        [st.session_state.store[sec], pd.DataFrame([row_dict])],
        ignore_index=True
    )

def del_selected(sec):
    sel = st.session_state.row_sel[sec]
    if sel is not None and sel < len(st.session_state.store[sec]):
        st.session_state.store[sec].drop(index=sel, inplace=True)
        st.session_state.store[sec].reset_index(drop=True, inplace=True)
        st.session_state.row_sel[sec] = None

# ── Individual tab ─────────────────────────────────────────────────────────
tabs = st.tabs([
    "Individual", "Phenotypic Feature", "Disease", "Measurement",
    "Biosample", "Genomic Interpretation", "Medical Action", "Pedigree", "Download"
])

with tabs[0]:
    st.subheader("Individual")
    ind_id = st.text_input("Individual ID", key="Ind_ID")
    ind_age = st.number_input("Age (days)", min_value=0, step=1, key="Ind_AgeDays")
    ind_sex   = st.selectbox("Sex",   dd["Ind_Sex"], key="Ind_Sex")
    ind_ksex  = st.selectbox("Karyotypic Sex", dd["Ind_KSex"], key="Ind_KSex")
    ind_vital = st.selectbox("Vital Status",    dd["Ind_Vital"], key="Ind_Vital")
    ind_last = st.time_input("Last Encounter (24 h)", value=time(0, 0), key="Ind_Last")

# ── helper to build each data-entry tab ------------------------------------
def section_page(tab, key, title, mapping=None):
    if mapping is None: mapping = {}
    with tab:
        st.subheader(title)
        cols = fields[key]
        inputs = {}
        for col in cols:
            fld = f"{key}_{col}"
            if col == "IndividualID":
                st.text_input(col, value=ind_id, disabled=True, key=fld)
                inputs[col] = ind_id
            elif col in mapping:
                inputs[col] = st.selectbox(col, dd[mapping[col]], key=fld)
            else:
                inputs[col] = st.text_input(col, key=fld)

        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"Add to {title}", key=f"add_{key}"):
                add_row(key, inputs)
        with c2:
            if st.button("Delete selected", key=f"del_{key}"):
                del_selected(key)

        df = st.session_state.store[key]
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.session_state.row_sel[key] = st.number_input(
                "Row index to delete", min_value=0, max_value=len(df)-1,
                step=1, key=f"rowpick_{key}"
            )

# ── build each section tab --------------------------------------------------
section_page(tabs[1], "PF",  "Phenotypic Feature",
             mapping=dict(Excluded="PF_Excluded", Severity="PF_Severity"))
section_page(tabs[2], "D",   "Disease",
             mapping=dict(ClinicalStatus="D_Status", Severity="D_Severity"))
section_page(tabs[3], "M",   "Measurement",
             mapping=dict(Interpretation="M_Interp"))
section_page(tabs[4], "B",   "Biosample")
section_page(tabs[5], "G",   "Genomic Interpretation",
             mapping=dict(Zygosity="G_Zygosity", Pathogenicity="G_Pathogenicity",
                          InterpretStatus="G_IStatus", Actionability="G_Action"))
section_page(tabs[6], "Med", "Medical Action",
             mapping=dict(Type="Med_Type"))
section_page(tabs[7], "P",   "Pedigree",
             mapping=dict(Relation="P_Relation", Affected="P_Affected",
                          Sex="P_Sex", Deceased="P_Deceased"))

# ── Download tab ------------------------------------------------------------
with tabs[8]:
    st.subheader("Download all data (single CSV)")
    if st.button("Generate & Download"):
        frames = []
        for sec, df in st.session_state.store.items():
            if not df.empty:
                out = df.copy()
                out["Section"] = sec
                frames.append(out)
        if frames:
            csv_buf = StringIO()
            pd.concat(frames).to_csv(csv_buf, index=False)
            csv_buf.seek(0)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_buf.getvalue(),
                file_name=f"phenopacket_{datetime.now().date()}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data to export yet.")
