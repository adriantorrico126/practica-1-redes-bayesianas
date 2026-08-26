"""Analisis reproducible de churn con redes bayesianas discretas."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / ".pgmpy_default"))

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from pgmpy.estimators import BayesianEstimator, BicScore, HillClimbSearch
from pgmpy.inference import VariableElimination
from pgmpy.models import BayesianNetwork
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).parent
OUT = ROOT / "resultados"
OUT.mkdir(exist_ok=True)
RANDOM_STATE = 42


def discretizar(df):
    d = df.copy()
    d["Internet_Service"] = d["Internet_Service"].fillna("Unknown")
    d["Age_Group"] = pd.cut(d["Age"], [17, 30, 45, 60, 70], labels=["Young", "Adult", "Mature", "Senior"], include_lowest=True).astype(str)
    d["Tenure_Group"] = pd.cut(d["Tenure_Months"], [-1, 12, 24, 48, np.inf], labels=["Low", "Medium", "Established", "Loyal"], include_lowest=True).astype(str)
    d["Amount_Group"] = pd.qcut(d["Monthly_Amount"], q=3, labels=["Low", "Medium", "High"], duplicates="drop").astype(str)
    d["Complaints_Group"] = pd.cut(d["Complaints"], [-1, 0, 2, np.inf], labels=["None", "Few", "Many"], include_lowest=True).astype(str)
    d["Satisfaction_Group"] = pd.cut(d["Satisfaction"], [0, 4, 7, 10], labels=["Low", "Medium", "High"], include_lowest=True).astype(str)
    cols = ["Age_Group", "Tenure_Group", "Amount_Group", "Contract_Type", "Payment_Method", "Technical_Support", "Internet_Service", "Complaints_Group", "Satisfaction_Group", "Churn"]
    return d, d[cols].astype(str)


def plot_eda(raw, disc):
    sns.set_theme(style="whitegrid", context="notebook")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    sns.countplot(data=raw, x="Churn", hue="Churn", ax=axes[0], palette={"No": "#3B82F6", "Yes": "#EF4444"}, legend=False)
    axes[0].set_title("Distribucion de abandono")
    axes[0].set_xlabel("Abandono")
    axes[0].set_ylabel("Clientes")
    rates = pd.crosstab(disc["Contract_Type"], disc["Churn"], normalize="index").mul(100).reset_index()
    rates.plot(x="Contract_Type", y="Yes", kind="bar", color="#EF4444", legend=False, ax=axes[1])
    axes[1].set_title("Tasa de abandono por contrato")
    axes[1].set_xlabel("Tipo de contrato")
    axes[1].set_ylabel("Abandono (%)")
    axes[1].tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(OUT / "eda_churn.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    sns.barplot(data=pd.crosstab(disc["Satisfaction_Group"], disc["Churn"], normalize="index").mul(100).reset_index(), x="Satisfaction_Group", y="Yes", order=["Low", "Medium", "High"], color="#F59E0B", ax=axes[0])
    axes[0].set_title("Abandono segun satisfaccion")
    axes[0].set_xlabel("Satisfaccion")
    axes[0].set_ylabel("Abandono (%)")
    sns.barplot(data=pd.crosstab(disc["Tenure_Group"], disc["Churn"], normalize="index").mul(100).reset_index(), x="Tenure_Group", y="Yes", order=["Low", "Medium", "Established", "Loyal"], color="#8B5CF6", ax=axes[1])
    axes[1].set_title("Abandono segun antiguedad")
    axes[1].set_xlabel("Antiguedad")
    axes[1].set_ylabel("Abandono (%)")
    fig.tight_layout()
    fig.savefig(OUT / "eda_riesgos.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_network(model, filename, title):
    fig, ax = plt.subplots(figsize=(10, 6))
    graph = nx.DiGraph(model.edges())
    pos = nx.spring_layout(graph, seed=RANDOM_STATE, k=1.3)
    nx.draw_networkx_nodes(graph, pos, node_color=["#EF4444" if n == "Churn" else "#DBEAFE" for n in graph.nodes()], edgecolors="#1E3A8A", node_size=2200, ax=ax)
    nx.draw_networkx_edges(graph, pos, edge_color="#64748B", arrowsize=22, width=1.5, ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=8, font_weight="bold", ax=ax)
    ax.set_title(title, fontweight="bold")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def evaluate(model, test):
    features = [c for c in test.columns if c != "Churn"]
    pred = model.predict(test[features])["Churn"]
    y = test["Churn"]
    return {
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "precision": round(float(precision_score(y, pred, pos_label="Yes", zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, pos_label="Yes", zero_division=0)), 4),
        "f1": round(float(f1_score(y, pred, pos_label="Yes", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y, pred, labels=["No", "Yes"]).tolist(),
        "classification_report": classification_report(y, pred, zero_division=0),
    }


def main():
    raw = pd.read_csv(ROOT / "customers (2).csv")
    enriched, data = discretizar(raw)
    plot_eda(raw, data)
    train, test = train_test_split(data, test_size=0.25, stratify=data["Churn"], random_state=RANDOM_STATE)

    manual_edges = [
        ("Age_Group", "Satisfaction_Group"), ("Amount_Group", "Satisfaction_Group"),
        ("Complaints_Group", "Satisfaction_Group"), ("Contract_Type", "Tenure_Group"),
        ("Contract_Type", "Churn"), ("Technical_Support", "Churn"),
        ("Satisfaction_Group", "Churn"), ("Tenure_Group", "Churn"),
        ("Complaints_Group", "Churn"), ("Internet_Service", "Churn"),
    ]
    manual = BayesianNetwork(manual_edges)
    manual.add_nodes_from(data.columns)
    manual.fit(train, estimator=BayesianEstimator, prior_type="BDeu", equivalent_sample_size=10)
    plot_network(manual, "red_manual.png", "Red Bayesiana propuesta")

    hc = HillClimbSearch(train)
    learned = hc.estimate(scoring_method=BicScore(train), max_indegree=3, max_iter=1000, show_progress=False)
    automatic = BayesianNetwork(learned.edges())
    automatic.add_nodes_from(data.columns)
    automatic.fit(train, estimator=BayesianEstimator, prior_type="BDeu", equivalent_sample_size=10)
    plot_network(automatic, "red_hillclimb.png", "Red Bayesiana aprendida con Hill Climbing")

    inference = VariableElimination(automatic)
    evidence = {"Contract_Type": "Monthly", "Technical_Support": "No", "Satisfaction_Group": "Low", "Tenure_Group": "Low"}
    query = inference.query(variables=["Churn"], evidence=evidence, show_progress=False)
    states = list(query.state_names["Churn"])
    probabilities = {state: round(float(query.values[i]), 4) for i, state in enumerate(states)}

    result = {
        "n_rows": int(raw.shape[0]), "n_columns": int(raw.shape[1]),
        "missing_internet_service": int(raw["Internet_Service"].isna().sum()),
        "churn_counts": raw["Churn"].value_counts().to_dict(),
        "churn_rate": round(float((raw["Churn"] == "Yes").mean()), 4),
        "numeric_summary": raw[["Age", "Tenure_Months", "Monthly_Amount", "Complaints", "Satisfaction"]].describe().round(2).to_dict(),
        "risk_rates": {
            "contract": (pd.crosstab(data["Contract_Type"], data["Churn"], normalize="index")["Yes"] * 100).round(2).to_dict(),
            "support": (pd.crosstab(data["Technical_Support"], data["Churn"], normalize="index")["Yes"] * 100).round(2).to_dict(),
            "satisfaction": (pd.crosstab(data["Satisfaction_Group"], data["Churn"], normalize="index")["Yes"] * 100).round(2).to_dict(),
            "tenure": (pd.crosstab(data["Tenure_Group"], data["Churn"], normalize="index")["Yes"] * 100).round(2).to_dict(),
        },
        "manual_edges": [list(x) for x in manual.edges()],
        "automatic_edges": [list(x) for x in automatic.edges()],
        "manual_metrics": evaluate(manual, test),
        "automatic_metrics": evaluate(automatic, test),
        "inference_evidence": evidence, "inference_probabilities": probabilities,
        "train_rows": int(len(train)), "test_rows": int(len(test)),
        "manual_cpds": [str(cpd) for cpd in manual.get_cpds()],
        "automatic_cpds": [str(cpd) for cpd in automatic.get_cpds()],
    }
    with open(OUT / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    pd.DataFrame({"Variable": data.columns, "Categorías": [", ".join(sorted(data[c].unique())) for c in data.columns]}).to_csv(OUT / "categorias.csv", index=False, encoding="utf-8-sig")
    print(json.dumps({k: result[k] for k in ["churn_rate", "manual_metrics", "automatic_metrics", "inference_probabilities", "automatic_edges"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
