"""Taller 3: Box plot mensual de la TRM diaria USD/COP, generado con Matplotlib."""
from pathlib import Path
import base64, json, re
import pandas as pd
import matplotlib.pyplot as plt

CARPETA = Path(__file__).resolve().parent
ARCHIVO = CARPETA / "trm_diaria_2022_2026.csv"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

def cargar_trm():
    """Lee una fila por fecha de certificación TRM (no inventa valores en festivos)."""
    df = pd.read_csv(ARCHIVO, parse_dates=["fecha_desde", "fecha_hasta"])
    df["valor"] = pd.to_numeric(df["trm_cop_por_usd"])
    df["anio"] = df["fecha_desde"].dt.year
    df["mes"] = df["fecha_desde"].dt.month
    return df

def dibujar_boxplot(df, anio, destino=None):
    """Matplotlib boxplot mensual: mediana, Q1/Q3, bigotes 1.5×IQR y atípicos."""
    parte = df[df.anio == anio]
    datos = [parte.loc[parte.mes == m, "valor"].to_numpy() for m in range(1, 13)]
    fig, ax = plt.subplots(figsize=(12.5, 4.3), dpi=150)
    ax.boxplot(datos, tick_labels=MESES, patch_artist=True, showfliers=True,
        medianprops={"color":"#142d4e", "linewidth":2},
        boxprops={"facecolor":"#72c9ba", "edgecolor":"#168b80"},
        whiskerprops={"color":"#168b80"}, capprops={"color":"#168b80"})
    ax.set_title(f"Distribución mensual de la TRM · {anio}", loc="left")
    ax.set_xlabel("Mes"); ax.set_ylabel("COP por USD")
    ax.grid(axis="y", alpha=.2); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    if destino: fig.savefig(destino, dpi=180, bbox_inches="tight")
    return fig

def generar_dashboard(df):
    """Regenera los box plots SVG anuales e inyecta datos en el dashboard interactivo."""
    boxes = {}
    for anio in sorted(df.anio.unique()):
        fig = dibujar_boxplot(df, int(anio))
        buffer = __import__("io").BytesIO()
        fig.savefig(buffer, format="svg", bbox_inches="tight")
        plt.close(fig)
        boxes[str(int(anio))] = base64.b64encode(buffer.getvalue()).decode("ascii")
    rates = df.copy()
    rates["mes_label"] = rates.fecha_desde.dt.strftime("%b")
    payload = json.dumps(rates.assign(fecha=rates.fecha_desde.dt.strftime("%Y-%m-%d"))[["valor", "anio", "mes", "mes_label", "fecha"]].to_dict(orient="records"), ensure_ascii=False)
    years = sorted(int(y) for y in rates.anio.unique())
    template = (CARPETA / "dashboard_trm_boxplot.html").read_text(encoding="utf-8")
    replacement = "const DATA=" + payload + ",BOXES=" + json.dumps(boxes) + ",YEARS=" + json.dumps(years) + ";const cop="
    template = re.sub(r"const DATA=.*?;const cop=", replacement, template, count=1, flags=re.S)
    (CARPETA / "dashboard_trm_boxplot.html").write_text(template, encoding="utf-8")
    print("Dashboard regenerado:", len(df), "certificaciones desde", df.fecha_desde.min().date(), "hasta", df.fecha_desde.max().date())

if __name__ == "__main__":
    generar_dashboard(cargar_trm())
