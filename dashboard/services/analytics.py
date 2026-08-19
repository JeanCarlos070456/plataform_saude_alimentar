from __future__ import annotations
import math, json
from statistics import NormalDist
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from django.core.cache import cache
from django.conf import settings
from .data_source import load_dataframe

VARIABLES = {
    "sex": ("Sexo", ["Feminino", "Masculino"]),
    "age_group": ("Faixa etária", ["7–9 anos", "10–11 anos", "12–14 anos", "15–17 anos"]),
    "shift": ("Turno escolar", ["Matutino", "Vespertino"]),
    "mother_education": ("Escolaridade materna", ["0–8 anos", "9–11 anos", "≥12 anos", "Não soube informar"]),
    "income_group": ("Renda familiar mensal", ["Até 1 SM", "1 a 2 SM", ">2 SM"]),
    "race_group": ("Raça/cor", ["Brancos", "Pardos/pretos", "Outras raças/cores"]),
}
REFERENCES = {
    "sex":"Feminino", "age_group":"7–9 anos", "shift":"Matutino",
    "mother_education":"≥12 anos", "income_group":">2 SM", "race_group":"Brancos",
}

def wilson(cases: int, total: int, confidence: float = .95) -> tuple[float, float]:
    if not total: return (float("nan"), float("nan"))
    z = NormalDist().inv_cdf(1 - (1-confidence)/2)
    p = cases/total
    den=1+z*z/total
    center=(p+z*z/(2*total))/den
    margin=(z*math.sqrt((p*(1-p)+z*z/(4*total))/total))/den
    return max(0,center-margin)*100, min(1,center+margin)*100

def fmt_pct(v): return "—" if pd.isna(v) else f"{v:.1f}%".replace(".",",")
def fmt_num(v,d=2): return "—" if pd.isna(v) else f"{v:.{d}f}".replace(".",",")
def fmt_p(v):
    if pd.isna(v): return "—"
    if v < .001: return "<0,001"
    return f"{v:.3f}".replace(".",",")

def prevalence_rows(df: pd.DataFrame, variable: str, outcome="any_insecurity") -> list[dict]:
    title, order = VARIABLES[variable]
    rows=[]
    valid=df[[variable,outcome]].dropna()
    for category in order:
        sub=valid[valid[variable]==category]
        n=len(sub); cases=int(sub[outcome].sum()) if n else 0
        pct=100*cases/n if n else np.nan
        lo,hi=wilson(cases,n)
        rows.append({"category":category,"n":n,"cases":cases,"prevalence":pct,"prevalence_fmt":fmt_pct(pct),"ci_low":lo,"ci_high":hi,"ci_fmt":f"{fmt_num(lo,1)}–{fmt_num(hi,1)}"})
    return rows


def age_prevalence_rows(df: pd.DataFrame, outcome="any_insecurity") -> list[dict]:
    """
    Estratificação etária usada apenas na tabela descritiva do painel.

    Regra:
    - 7 a 10 anos: 7 <= idade < 11
    - ≥ 11 anos: idade >= 11

    A variável original ``age_group`` permanece intacta e continua sendo usada
    no modelo inferencial/associações, preservando o baseline validado.
    """
    valid = df[["age_years", outcome]].copy()
    valid["age_years"] = pd.to_numeric(valid["age_years"], errors="coerce")
    valid[outcome] = pd.to_numeric(valid[outcome], errors="coerce")
    valid = valid.dropna(subset=["age_years", outcome])

    groups = [
        ("7 a 10 anos", (valid["age_years"] >= 7) & (valid["age_years"] < 11)),
        ("≥ 11 anos", valid["age_years"] >= 11),
    ]

    rows = []
    for category, mask in groups:
        sub = valid.loc[mask]
        n = len(sub)
        cases = int(sub[outcome].sum()) if n else 0
        pct = 100 * cases / n if n else np.nan
        lo, hi = wilson(cases, n)

        rows.append({
            "category": category,
            "n": n,
            "cases": cases,
            "prevalence": pct,
            "prevalence_fmt": fmt_pct(pct),
            "ci_low": lo,
            "ci_high": hi,
            "ci_fmt": f"{fmt_num(lo, 1)}–{fmt_num(hi, 1)}",
        })

    return rows


def level_distribution(df):
    order=["Sem insegurança","Algum risco","Risco moderado/grave"]
    valid=df["insecurity_level"].dropna(); n=len(valid)
    return [{"label":x,"n":int((valid==x).sum()),"pct":100*(valid==x).sum()/n if n else 0} for x in order]

def _crude_ratio(rows, reference):
    ref=next((r for r in rows if r["category"]==reference),None)
    result=[]
    for r in rows:
        if not r["n"] or not ref or not ref["n"]:
            result.append((np.nan,np.nan,np.nan)); continue
        if r["category"]==reference:
            result.append((1.0,1.0,1.0)); continue
        p1=r["cases"]/r["n"]; p0=ref["cases"]/ref["n"]
        if p1<=0 or p0<=0:
            result.append((np.nan,np.nan,np.nan)); continue
        rp=p1/p0
        se=math.sqrt((1-r["cases"]/r["n"])/max(r["cases"],1)+(1-ref["cases"]/ref["n"])/max(ref["cases"],1))
        result.append((rp, math.exp(math.log(rp)-1.96*se), math.exp(math.log(rp)+1.96*se)))
    return result

def adjusted_model(df: pd.DataFrame):
    cols=["any_insecurity","sex","age_group","shift","mother_education","income_group","race_group","school_code"]
    model_df=df[cols].dropna().copy()
    model_df=model_df[model_df["mother_education"]!="Não soube informar"]
    formula=("any_insecurity ~ C(sex, Treatment(reference='Feminino')) + "
             "C(age_group, Treatment(reference='7–9 anos')) + "
             "C(shift, Treatment(reference='Matutino')) + "
             "C(mother_education, Treatment(reference='≥12 anos')) + "
             "C(income_group, Treatment(reference='>2 SM')) + "
             "C(race_group, Treatment(reference='Brancos')) + C(school_code)")
    fit=smf.glm(formula=formula,data=model_df,family=sm.families.Poisson()).fit(cov_type="HC0")
    ci=fit.conf_int()
    return fit,ci,len(model_df)

def _find_param(fit, variable, category):
    tokens={
      "sex":"C(sex", "age_group":"C(age_group", "shift":"C(shift",
      "mother_education":"C(mother_education", "income_group":"C(income_group", "race_group":"C(race_group"
    }
    for name in fit.params.index:
        if tokens[variable] in name and f"[T.{category}]" in name: return name
    return None

def association_table(df):
    try: fit,ci,model_n=adjusted_model(df)
    except Exception: fit=ci=None; model_n=0
    output=[]
    for variable,(title,order) in VARIABLES.items():
        rows=prevalence_rows(df,variable)
        crudes=_crude_ratio(rows,REFERENCES[variable])
        for row,(crp,cl,ch) in zip(rows,crudes):
            cat=row["category"]; ref=cat==REFERENCES[variable]
            if ref:
                arp=al=ah=1.0; p=np.nan
            elif fit is not None:
                param=_find_param(fit,variable,cat)
                if param:
                    arp=float(np.exp(fit.params[param])); al=float(np.exp(ci.loc[param,0])); ah=float(np.exp(ci.loc[param,1])); p=float(fit.pvalues[param])
                else: arp=al=ah=p=np.nan
            else: arp=al=ah=p=np.nan
            output.append({
                "variable":title,"variable_key":variable,"category":cat,"reference":ref,
                "crude_rp":crp,"crude_rp_fmt":"1,00" if ref else fmt_num(crp),
                "crude_ci_fmt":"Referência" if ref else f"{fmt_num(cl)}–{fmt_num(ch)}",
                "adjusted_rp":arp,"adjusted_rp_fmt":"1,00" if ref else fmt_num(arp),
                "adjusted_low":al,"adjusted_high":ah,
                "adjusted_ci_fmt":"Referência" if ref else f"{fmt_num(al)}–{fmt_num(ah)}",
                "p":p,"p_fmt":"—" if ref else fmt_p(p),
            })
    if settings.CAAFE_MODEL_MODE == "validated":
        try:
            baseline=json.loads((settings.DATA_DIR/"baseline_metrics.json").read_text(encoding="utf-8"))
            for row in output:
                if row["reference"]: continue
                saved=baseline.get("associations",{}).get(f"{row['variable_key']}|{row['category']}")
                if not saved: continue
                crp,cl,ch=saved["crude"]; arp,al,ah=saved["adjusted"]; p=saved["p"]
                row.update({"crude_rp":crp,"crude_rp_fmt":fmt_num(crp),"crude_ci_fmt":f"{fmt_num(cl)}–{fmt_num(ch)}",
                            "adjusted_rp":arp,"adjusted_rp_fmt":fmt_num(arp),"adjusted_low":al,"adjusted_high":ah,
                            "adjusted_ci_fmt":f"{fmt_num(al)}–{fmt_num(ah)}","p":p,"p_fmt":fmt_p(p)})
            model_n=int(baseline.get("model_n_report",model_n))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return output,model_n

def school_summary(df):
    rows=[]
    for code,sub in df.groupby("school_code",dropna=True):
        valid=sub.dropna(subset=["any_insecurity"]); n=len(valid); cases=int(valid["any_insecurity"].sum()) if n else 0
        m=int(valid["moderate_severe"].sum()) if n else 0
        lo,hi=wilson(cases,n)
        low_income=sub["income_group"].eq("Até 1 SM").mean()*100
        low_edu=sub["mother_education"].eq("0–8 anos").mean()*100
        pp=sub["race_group"].eq("Pardos/pretos").mean()*100
        rows.append({
            "school_code":int(code),"school_name":sub["school_name"].dropna().iloc[0] if sub["school_name"].notna().any() else f"Escola {code}",
            "n_valid":n,"cases":cases,"prevalence":100*cases/n if n else np.nan,"ci_low":lo,"ci_high":hi,
            "moderate_severe":100*m/n if n else np.nan,"low_income":low_income,"low_mother_education":low_edu,
            "black_brown":pp,"mean_age":sub["age_years"].mean(),"female":sub["sex"].eq("Feminino").mean()*100,
        })
    return rows

def build_payload(force=False):
    df,status=load_dataframe(force=force)
    key=f"caafe-payload-v2-{status.hash}"
    if not force and (saved:=cache.get(key)): return saved
    valid=df.dropna(subset=["any_insecurity"])
    n=len(valid); cases=int(valid["any_insecurity"].sum()); ms=int(valid["moderate_severe"].sum())
    lo,hi=wilson(cases,n); mslo,mshi=wilson(ms,n)
    associations,model_n=association_table(df)
    tables = {
        k: {
            "title": title,
            "rows": age_prevalence_rows(df) if k == "age_group" else prevalence_rows(df, k),
        }
        for k, (title, _) in VARIABLES.items()
    }
    payload={
        "source":{"type":status.source,"hash":status.hash[:12],"rows":status.rows,"updated_at":status.updated_at},
        "summary":{"valid_n":n,"cases":cases,"prevalence":100*cases/n,"prevalence_fmt":fmt_pct(100*cases/n),
                   "ci_fmt":f"{fmt_num(lo,1)}–{fmt_num(hi,1)}", "moderate_severe_n":ms,
                   "moderate_severe_pct":100*ms/n,"moderate_severe_fmt":fmt_pct(100*ms/n),
                   "moderate_severe_ci_fmt":f"{fmt_num(mslo,1)}–{fmt_num(mshi,1)}","model_n":model_n},
        "tables":tables,"associations":associations,"levels":level_distribution(df),"schools":school_summary(df),
    }
    cache.set(key,payload,timeout=None)
    return payload