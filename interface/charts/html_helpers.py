"""
charts/html_helpers.py — CSS, Layout Plotly, Badges e Funções Auxiliares HTML.
Builder Pattern: cada função constrói um fragmento HTML independente e reutilizável.
"""

import statistics
import html as html_module

# ============================================================================
# CSS — Tema Dark Premium
# ============================================================================

INSIGHTS_CSS = """
<style>
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.insights-container {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0;
}
.chart-section { margin-bottom: 24px; animation: fadeInUp 0.6s ease-out both; }
.chart-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #334155;
    transition: all 0.3s ease;
}
.chart-card:hover {
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
    transform: translateY(-2px);
}
.explain-box {
    background: rgba(15,23,42,0.7);
    border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-top: 10px;
    font-size: 0.82rem;
    color: #94a3b8;
    line-height: 1.5;
}
.explain-box b { color: #a5b4fc; }
.stats-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 2px 3px;
    position: relative;
    cursor: help;
}
.stats-badge:hover::after {
    content: attr(data-tip);
    position: absolute;
    bottom: 110%;
    left: 50%;
    transform: translateX(-50%);
    background: #0f172a;
    color: #e2e8f0;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 400;
    white-space: normal;
    width: 260px;
    text-align: center;
    line-height: 1.4;
    z-index: 9999;
    border: 1px solid #475569;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    animation: fadeInUp 0.15s ease-out;
    pointer-events: none;
}
.odd-badge {
    background: rgba(234,179,8,0.15);
    color: #fbbf24;
    border: 1px solid rgba(234,179,8,0.3);
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    display: inline-block;
    margin: 2px 4px;
}
.glossary-term {
    color: #e2e8f0;
    font-weight: 700;
}
.glossary-desc {
    color: #94a3b8;
    font-size: 0.85rem;
}
.bet-entry details {
    margin: 3px 0;
}
.bet-entry summary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s ease;
    list-style: none;
}
.bet-entry summary::-webkit-details-marker { display: none; }
.bet-entry summary::before { content: '▶ '; font-size: 0.65rem; }
.bet-entry details[open] summary::before { content: '▼ '; }
.bet-entry summary:hover { transform: scale(1.02); filter: brightness(1.15); }
.bet-low summary { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.bet-med summary { background: rgba(234,179,8,0.15); color: #fbbf24; border: 1px solid rgba(234,179,8,0.3); }
.bet-high summary { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.bet-detail {
    background: rgba(15,23,42,0.9);
    border: 1px solid #475569;
    border-radius: 10px;
    padding: 14px 16px;
    margin: 6px 0 4px 0;
    font-size: 0.82rem;
    color: #cbd5e1;
    line-height: 1.6;
    animation: fadeInUp 0.2s ease-out;
}
</style>
"""


# ============================================================================
# Plotly Layout & Conversion
# ============================================================================

def base_layout(title="", height=400):
    """Retorna dict de layout padrão Plotly com tema dark."""
    return dict(
        title=dict(text=title, font=dict(size=16, color="#e2e8f0")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.8)",
        font=dict(color="#cbd5e1", family="Segoe UI, system-ui, sans-serif"),
        height=height,
        margin=dict(l=50, r=30, t=50, b=40),
        xaxis=dict(gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155"),
        yaxis=dict(gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155"),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )


def fig_to_html(fig):
    """Converte uma Plotly Figure em iframe HTML seguro para Gradio."""
    raw = fig.to_html(
        full_html=True, include_plotlyjs="cdn",
        config={"displayModeBar": True, "scrollZoom": True, "responsive": True,
                "modeBarButtonsToRemove": ["sendDataToCloud", "editInChartStudio", "lasso2d"]},
    )
    escaped = html_module.escape(raw)
    height = fig.layout.height or 400
    return f'<iframe srcdoc="{escaped}" style="width:100%;height:{height + 50}px;border:none;background:transparent;" scrolling="no"></iframe>'


# ============================================================================
# Data Conversion Helpers
# ============================================================================

def int_list(data):
    """Filtra None e converte para lista de inteiros."""
    return [int(round(v)) for v in data if v is not None]


def float_list(data):
    """Filtra None e converte para lista de floats."""
    return [float(v) for v in data if v is not None]


# ============================================================================
# Statistics
# ============================================================================

def calc_stats(data):
    """Calcula estatísticas descritivas completas: μ, Med, σ, Min, Max, Moda, P25, P75."""
    if not data:
        return {}
    clean = [v for v in data if v is not None]
    if not clean:
        return {}
    n = len(clean)
    avg = sum(clean) / n
    med = statistics.median(clean)
    try:
        mode_val = statistics.mode([round(v, 1) for v in clean])
    except statistics.StatisticsError:
        mode_val = avg
    std = statistics.stdev(clean) if n > 1 else 0
    sorted_d = sorted(clean)
    p25 = sorted_d[max(0, int(n * 0.25))]
    p75 = sorted_d[min(n - 1, int(n * 0.75))]
    return {"avg": avg, "med": med, "std": std, "min": min(clean), "max": max(clean),
            "mode": mode_val, "p25": p25, "p75": p75, "n": n}


# ============================================================================
# HTML Badge Builders
# ============================================================================

def stats_html(st, unit=""):
    """Gera badges HTML com tooltips para cada estatística."""
    if not st:
        return ""
    u = unit
    return (
        f'<span class="stats-badge" style="background:rgba(59,130,246,0.15);color:#60a5fa;" data-tip="Média (μ): Valor central de todos os dados. Em LoL, indica a tendência de longo prazo do time.">μ={st["avg"]:.1f}{u}</span>'
        f'<span class="stats-badge" style="background:rgba(168,85,247,0.15);color:#c084fc;" data-tip="Mediana: O valor do meio quando os dados são ordenados. Menos afetada por jogos extremos (stomps ou derrotas pesadas).">Med={st["med"]:.1f}{u}</span>'
        f'<span class="stats-badge" style="background:rgba(34,197,94,0.15);color:#4ade80;" data-tip="Desvio Padrão (σ): Mede a consistência. σ baixo = time previsível, σ alto = resultados voláteis (bom para apostas de risco).">σ={st["std"]:.1f}</span>'
        f'<span class="stats-badge" style="background:rgba(234,179,8,0.12);color:#fbbf24;" data-tip="Min/Max: Os extremos históricos. Mostra o pior e o melhor desempenho do time nesta métrica.">Min={st["min"]:.0f} Max={st["max"]:.0f}</span>'
        f'<span class="stats-badge" style="background:rgba(99,102,241,0.15);color:#818cf8;" data-tip="Moda: O valor que mais se repete. Em LoL, indica o resultado \'típico\' da equipe.">Moda={st["mode"]:.1f}</span>'
        f'<span class="stats-badge" style="background:rgba(236,72,153,0.12);color:#f472b6;" data-tip="Percentis 25/75: 50% dos resultados caem entre P25 e P75. É a faixa \'normal\' de desempenho.">P25={st["p25"]:.1f} P75={st["p75"]:.1f}</span>'
    )


def odd_badge(prob):
    """Gera badge amarelo com a odd ideal baseada na probabilidade."""
    if not prob or prob <= 0:
        return ""
    odd = 100 / prob
    return f'<span class="odd-badge">💰 Odd ideal: {odd:.2f} (prob. {prob:.0f}%)</span>'


def explain(text):
    """Gera caixa explicativa '📖 Como ler:' com bordas indigo."""
    return f'<div class="explain-box">📖 <b>Como ler:</b> {text}</div>'


def risk_tier(prob):
    """Classifica probabilidade em tier de risco: low (≥65%), med (50-64%), high (<50%)."""
    if prob >= 65:
        return ("low", "🟢 Baixo Risco")
    if prob >= 50:
        return ("med", "🟡 Risco Médio")
    return ("high", "🔴 Alto Risco")


def bet_line(team, market, line, prob, data_points, explanation):
    """Gera um card de aposta com details/summary nativo (funciona sem JS)."""
    if prob is None or prob <= 0:
        return ""
    odd = 100 / prob
    tier, label = risk_tier(prob)
    return (
        f'<div class="bet-entry bet-{tier}">'
        f'<details>'
        f'<summary>{team} — {market} {line} @ <b>{odd:.2f}x</b> ({prob:.0f}%) [{label}]</summary>'
        f'<div class="bet-detail">'
        f'<b>📊 Detalhamento do Cálculo:</b><br>'
        f'<b>Mercado:</b> {market} {line}<br>'
        f'<b>Time:</b> {team}<br>'
        f'<b>Probabilidade Empírica:</b> {prob:.1f}% (baseada em {data_points} jogos reais)<br>'
        f'<b>Odd Justa (matemática):</b> 1 / ({prob:.1f}% / 100) = <b>{odd:.2f}</b><br>'
        f'<b>Classificação de Risco:</b> {label}<br><br>'
        f'<b>💡 Por que esse risco?</b><br>{explanation}<br><br>'
        f'<b>📐 Fórmula:</b> Odd = 100 / Prob%. Se a casa oferece odd &gt; {odd:.2f}, há <b>Expected Value positivo (+EV)</b>.'
        f'</div></details></div>'
    )
