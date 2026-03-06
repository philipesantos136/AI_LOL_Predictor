"""
Módulo de Geração de Gráficos — Insights com Dados Silver + BetBoom
Gera gráficos Plotly dinâmicos usando dados históricos reais da camada Silver,
com análise de valor opcional quando odds do BetBoom estão disponíveis.
"""

import sqlite3
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================================
# CSS — Tema Dark Premium com Animações
# ============================================================================

INSIGHTS_CSS = """
<style>
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 15px rgba(59, 130, 246, 0.2); }
    50% { box-shadow: 0 0 30px rgba(59, 130, 246, 0.4); }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

.insights-container {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0;
}

.insights-header {
    text-align: center;
    padding: 30px 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid rgba(59, 130, 246, 0.3);
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.5s ease-out;
}

.insights-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
    animation: pulseGlow 4s ease-in-out infinite;
}

.insights-header h2 {
    margin: 0 0 8px 0;
    font-size: 1.5rem;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
}

.insights-header .matchup {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: rgba(30, 41, 59, 0.8);
    padding: 8px 24px;
    border-radius: 50px;
    border: 1px solid rgba(59, 130, 246, 0.2);
    position: relative;
}

.team-blue { color: #60a5fa; font-weight: 700; font-size: 1.1rem; }
.team-red { color: #f87171; font-weight: 700; font-size: 1.1rem; }
.vs-text { color: #eab308; font-weight: 800; font-size: 0.9rem; }

.stats-row {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 16px;
    position: relative;
}

.stat-card {
    background: rgba(30, 41, 59, 0.6);
    padding: 12px 20px;
    border-radius: 12px;
    border: 1px solid rgba(59, 130, 246, 0.15);
    text-align: center;
    min-width: 100px;
}

.stat-value {
    font-size: 1.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.stat-label {
    color: #94a3b8;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
}

.chart-section {
    margin-bottom: 24px;
    animation: fadeInUp 0.6s ease-out both;
}
.chart-section:nth-child(2) { animation-delay: 0.1s; }
.chart-section:nth-child(3) { animation-delay: 0.2s; }
.chart-section:nth-child(4) { animation-delay: 0.3s; }
.chart-section:nth-child(5) { animation-delay: 0.4s; }
.chart-section:nth-child(6) { animation-delay: 0.5s; }

.section-title {
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 12px;
    padding-left: 12px;
    border-left: 3px solid #3b82f6;
}

.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    gap: 20px;
}

.chart-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #334155;
    transition: all 0.3s ease;
    overflow: hidden;
}

.chart-card:hover {
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
    transform: translateY(-2px);
}

.value-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
}

.value-good { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
.value-bad { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.value-neutral { background: rgba(234, 179, 8, 0.2); color: #fbbf24; border: 1px solid rgba(234, 179, 8, 0.3); }

.footer-note {
    text-align: center;
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 20px;
    padding: 12px;
}
</style>
"""


# ============================================================================
# Helpers
# ============================================================================

def _get_db_path():
    """Retorna o caminho do banco de dados."""
    # Tenta encontrar a partir de diferentes locais de execução
    candidates = [
        os.path.join("data", "db", "lol_datamatches.db"),
        os.path.join("..", "data", "db", "lol_datamatches.db"),
        os.path.join(os.path.dirname(__file__), "..", "data", "db", "lol_datamatches.db"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]  # fallback


def _base_layout(title="", height=400):
    """Layout base Plotly com tema dark."""
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


def _fig_to_html(fig):
    """Converte Figure Plotly para HTML renderizável dentro do Gradio.
    Usa iframe com srcdoc porque Gradio bloqueia <script> tags no gr.HTML."""
    import html as html_module
    
    raw_html = fig.to_html(
        full_html=True,
        include_plotlyjs="cdn",
        config={"displayModeBar": False, "responsive": True},
    )
    
    # Escapa o HTML para uso como srcdoc do iframe
    escaped = html_module.escape(raw_html)
    height = fig.layout.height or 400
    
    return f'<iframe srcdoc="{escaped}" style="width:100%;height:{height + 40}px;border:none;background:transparent;" scrolling="no"></iframe>'


# ============================================================================
# Queries no Banco Silver
# ============================================================================

def _get_team_stats(team_name):
    """
    Consulta o banco Silver e retorna stats agregadas de um time.
    Retorna dict com todas as métricas relevantes.
    """
    db_path = _get_db_path()
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Stats de time (position='team')
        c.execute("""
            SELECT 
                COUNT(DISTINCT gameid) as total_games,
                SUM(CASE WHEN result='1' THEN 1 ELSE 0 END) as wins,
                AVG(teamkills) as avg_kills,
                AVG(teamdeaths) as avg_deaths,
                AVG(dragons) as avg_dragons,
                AVG(towers) as avg_towers,
                AVG(barons) as avg_barons,
                AVG(heralds) as avg_heralds,
                AVG(gamelength) as avg_duration,
                AVG(CASE WHEN firstblood=1 THEN 1.0 ELSE 0.0 END) as fb_rate,
                AVG(CASE WHEN firstdragon=1 THEN 1.0 ELSE 0.0 END) as fd_rate,
                AVG(CASE WHEN firstbaron=1 THEN 1.0 ELSE 0.0 END) as fbaron_rate,
                AVG(CASE WHEN firstherald=1 THEN 1.0 ELSE 0.0 END) as fherald_rate,
                AVG(totalgold) as avg_gold,
                AVG(inhibitors) as avg_inhibitors,
                MIN(teamkills) as min_kills,
                MAX(teamkills) as max_kills,
                AVG(teamkills - teamdeaths) as avg_kill_diff
            FROM match_data_silver 
            WHERE position='team' AND teamname = ?
        """, (team_name,))
        
        row = c.fetchone()
        
        if not row or not row[0]:
            conn.close()
            return None
        
        stats = {
            "total_games": row[0],
            "wins": row[1],
            "win_rate": (row[1] / row[0] * 100) if row[0] else 0,
            "avg_kills": row[2] or 0,
            "avg_deaths": row[3] or 0,
            "avg_dragons": row[4] or 0,
            "avg_towers": row[5] or 0,
            "avg_barons": row[6] or 0,
            "avg_heralds": row[7] or 0,
            "avg_duration_s": row[8] or 0,
            "avg_duration_min": (row[8] or 0) / 60,
            "fb_rate": (row[9] or 0) * 100,
            "fd_rate": (row[10] or 0) * 100,
            "fbaron_rate": (row[11] or 0) * 100,
            "fherald_rate": (row[12] or 0) * 100,
            "avg_gold": row[13] or 0,
            "avg_inhibitors": row[14] or 0,
            "min_kills": row[15] or 0,
            "max_kills": row[16] or 0,
            "avg_kill_diff": row[17] or 0,
        }
        
        # Distribuição de kills (últimos jogos)
        c.execute("""
            SELECT teamkills FROM match_data_silver 
            WHERE position='team' AND teamname = ?
            ORDER BY gameid DESC LIMIT 20
        """, (team_name,))
        stats["kills_history"] = [r[0] for r in c.fetchall()]
        
        # Distribuição de dragões
        c.execute("""
            SELECT dragons FROM match_data_silver 
            WHERE position='team' AND teamname = ?
            ORDER BY gameid DESC LIMIT 20
        """, (team_name,))
        stats["dragons_history"] = [r[0] for r in c.fetchall()]
        
        # Distribuição de torres
        c.execute("""
            SELECT towers FROM match_data_silver 
            WHERE position='team' AND teamname = ?
            ORDER BY gameid DESC LIMIT 20
        """, (team_name,))
        stats["towers_history"] = [r[0] for r in c.fetchall()]
        
        # Win streak (últimos 10)
        c.execute("""
            SELECT result FROM match_data_silver 
            WHERE position='team' AND teamname = ?
            ORDER BY gameid DESC LIMIT 10
        """, (team_name,))
        stats["recent_results"] = [r[0] for r in c.fetchall()]
        
        conn.close()
        return stats
        
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar DB: {e}")
        return None


# ============================================================================
# Geração de Gráficos
# ============================================================================

def _gen_winrate_chart(s1, s2, t1, t2):
    """Gráfico de Win Rate comparativo com gauge duplo."""
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=[t1, t2]
    )
    
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=s1["win_rate"],
        number=dict(suffix="%", font=dict(size=36, color="#60a5fa")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#475569"),
            bar=dict(color="#3b82f6"),
            bgcolor="#1e293b",
            bordercolor="#334155",
            steps=[
                dict(range=[0, 40], color="rgba(239,68,68,0.15)"),
                dict(range=[40, 60], color="rgba(234,179,8,0.15)"),
                dict(range=[60, 100], color="rgba(34,197,94,0.15)"),
            ],
        ),
        delta=dict(reference=50, suffix="%"),
    ), row=1, col=1)
    
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=s2["win_rate"],
        number=dict(suffix="%", font=dict(size=36, color="#f87171")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#475569"),
            bar=dict(color="#ef4444"),
            bgcolor="#1e293b",
            bordercolor="#334155",
            steps=[
                dict(range=[0, 40], color="rgba(239,68,68,0.15)"),
                dict(range=[40, 60], color="rgba(234,179,8,0.15)"),
                dict(range=[60, 100], color="rgba(34,197,94,0.15)"),
            ],
        ),
        delta=dict(reference=50, suffix="%"),
    ), row=1, col=2)
    
    fig.update_layout(**_base_layout("🏆 Win Rate", height=300))
    fig.update_layout(
        annotations=[
            dict(text=t1, x=0.2, y=1.12, xref="paper", yref="paper",
                 showarrow=False, font=dict(size=14, color="#60a5fa")),
            dict(text=t2, x=0.8, y=1.12, xref="paper", yref="paper",
                 showarrow=False, font=dict(size=14, color="#f87171")),
        ]
    )
    return _fig_to_html(fig)


def _gen_radar_chart(s1, s2, t1, t2):
    """Radar chart de performance normalizada."""
    # Normalizar para escala 0-10
    max_kills = max(s1["avg_kills"], s2["avg_kills"], 1)
    max_dragons = max(s1["avg_dragons"], s2["avg_dragons"], 1)
    max_towers = max(s1["avg_towers"], s2["avg_towers"], 1)
    max_barons = max(s1["avg_barons"], s2["avg_barons"], 1)
    
    categories = ["Win Rate", "Kills", "Dragões", "Torres", "Barões", 
                   "First Blood", "First Dragon"]
    
    vals1 = [
        s1["win_rate"] / 10,
        s1["avg_kills"] / max_kills * 10,
        s1["avg_dragons"] / max_dragons * 10,
        s1["avg_towers"] / max_towers * 10,
        s1["avg_barons"] / max_barons * 10,
        s1["fb_rate"] / 10,
        s1["fd_rate"] / 10,
    ]
    vals2 = [
        s2["win_rate"] / 10,
        s2["avg_kills"] / max_kills * 10,
        s2["avg_dragons"] / max_dragons * 10,
        s2["avg_towers"] / max_towers * 10,
        s2["avg_barons"] / max_barons * 10,
        s2["fb_rate"] / 10,
        s2["fd_rate"] / 10,
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals1 + [vals1[0]], theta=categories + [categories[0]],
        fill="toself", fillcolor="rgba(59,130,246,0.15)",
        line=dict(color="#3b82f6", width=2),
        name=t1, marker=dict(size=6, color="#60a5fa"),
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals2 + [vals2[0]], theta=categories + [categories[0]],
        fill="toself", fillcolor="rgba(239,68,68,0.15)",
        line=dict(color="#ef4444", width=2),
        name=t2, marker=dict(size=6, color="#f87171"),
    ))
    
    layout = _base_layout("📊 Radar de Performance", height=420)
    layout["polar"] = dict(
        bgcolor="rgba(15,23,42,0.8)",
        radialaxis=dict(visible=True, range=[0, 10], gridcolor="rgba(51,65,85,0.5)",
                        tickfont=dict(size=10, color="#64748b")),
        angularaxis=dict(gridcolor="rgba(51,65,85,0.5)",
                         tickfont=dict(size=11, color="#cbd5e1")),
    )
    fig.update_layout(**layout)
    return _fig_to_html(fig)


def _gen_kills_comparison(s1, s2, t1, t2):
    """Box plot / histograma de distribuição de kills."""
    fig = go.Figure()
    
    if s1["kills_history"]:
        fig.add_trace(go.Box(
            y=s1["kills_history"], name=t1,
            marker_color="#3b82f6", line_color="#60a5fa",
            fillcolor="rgba(59,130,246,0.3)",
            boxpoints="all", jitter=0.3, pointpos=-1.8,
        ))
    if s2["kills_history"]:
        fig.add_trace(go.Box(
            y=s2["kills_history"], name=t2,
            marker_color="#ef4444", line_color="#f87171",
            fillcolor="rgba(239,68,68,0.3)",
            boxpoints="all", jitter=0.3, pointpos=-1.8,
        ))
    
    layout = _base_layout("⚔️ Distribuição de Kills (últimos 20 jogos)", height=380)
    layout["yaxis"]["title"] = "Kills por Jogo"
    fig.update_layout(**layout)
    return _fig_to_html(fig)


def _gen_objectives_chart(s1, s2, t1, t2):
    """Barras agrupadas de dragões, torres, barões, heralds."""
    categories = ["Dragões", "Torres", "Barões", "Arautos", "Inibidores"]
    vals1 = [s1["avg_dragons"], s1["avg_towers"], s1["avg_barons"], 
             s1["avg_heralds"], s1["avg_inhibitors"]]
    vals2 = [s2["avg_dragons"], s2["avg_towers"], s2["avg_barons"],
             s2["avg_heralds"], s2["avg_inhibitors"]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories, y=vals1, name=t1,
        marker=dict(color="#3b82f6", line=dict(color="#60a5fa", width=1)),
        text=[f"{v:.1f}" for v in vals1], textposition="outside",
        textfont=dict(color="#60a5fa", size=12),
    ))
    fig.add_trace(go.Bar(
        x=categories, y=vals2, name=t2,
        marker=dict(color="#ef4444", line=dict(color="#f87171", width=1)),
        text=[f"{v:.1f}" for v in vals2], textposition="outside",
        textfont=dict(color="#f87171", size=12),
    ))
    
    layout = _base_layout("🐉 Objetivos por Jogo (Média)", height=380)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "Média por Jogo"
    fig.update_layout(**layout)
    return _fig_to_html(fig)


def _gen_first_objectives_chart(s1, s2, t1, t2):
    """Indicadores de First Blood, First Dragon, First Baron."""
    categories = ["First Blood", "First Dragon", "First Baron", "First Herald"]
    vals1 = [s1["fb_rate"], s1["fd_rate"], s1["fbaron_rate"], s1["fherald_rate"]]
    vals2 = [s2["fb_rate"], s2["fd_rate"], s2["fbaron_rate"], s2["fherald_rate"]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories, y=vals1, name=t1,
        marker=dict(
            color=["rgba(59,130,246,0.8)"] * 4,
            line=dict(color="#60a5fa", width=1),
        ),
        text=[f"{v:.0f}%" for v in vals1], textposition="outside",
        textfont=dict(color="#60a5fa", size=12),
    ))
    fig.add_trace(go.Bar(
        x=categories, y=vals2, name=t2,
        marker=dict(
            color=["rgba(239,68,68,0.8)"] * 4,
            line=dict(color="#f87171", width=1),
        ),
        text=[f"{v:.0f}%" for v in vals2], textposition="outside",
        textfont=dict(color="#f87171", size=12),
    ))
    
    layout = _base_layout("🎯 Primeiros Objetivos (%)", height=380)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "% dos Jogos"
    layout["yaxis"]["range"] = [0, 105]
    fig.update_layout(**layout)
    return _fig_to_html(fig)


def _gen_recent_form(s1, s2, t1, t2):
    """Forma recente: últimos 10 resultados como heatmap."""
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">📈 Forma Recente (últimos 10 jogos)</h3>'
    
    for team_name, stats, color in [(t1, s1, "#3b82f6"), (t2, s2, "#ef4444")]:
        results = stats.get("recent_results", [])
        recent_wr = sum(1 for r in results if r == '1') / len(results) * 100 if results else 0
        
        html += f'<div style="margin-bottom:12px;">'
        html += f'<span style="color:{color};font-weight:700;font-size:0.95rem;">{team_name}</span>'
        html += f'<span style="color:#94a3b8;margin-left:8px;font-size:0.85rem;">(WR recente: {recent_wr:.0f}%)</span>'
        html += '<div style="display:flex;gap:4px;margin-top:6px;">'
        
        for r in results:
            if r == '1':
                html += '<div style="width:32px;height:32px;border-radius:6px;background:rgba(34,197,94,0.3);border:1px solid #22c55e;display:flex;align-items:center;justify-content:center;font-weight:700;color:#4ade80;font-size:0.8rem;">W</div>'
            else:
                html += '<div style="width:32px;height:32px;border-radius:6px;background:rgba(239,68,68,0.2);border:1px solid #ef4444;display:flex;align-items:center;justify-content:center;font-weight:700;color:#f87171;font-size:0.8rem;">L</div>'
        
        html += '</div></div>'
    
    html += '</div>'
    return html


def _gen_duration_chart(s1, s2, t1, t2):
    """Indicador de duração média."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[t1, t2],
        y=[s1["avg_duration_min"], s2["avg_duration_min"]],
        marker=dict(
            color=["#3b82f6", "#ef4444"],
            line=dict(color=["#60a5fa", "#f87171"], width=1.5),
        ),
        text=[f'{s1["avg_duration_min"]:.1f} min', f'{s2["avg_duration_min"]:.1f} min'],
        textposition="outside",
        textfont=dict(size=14, color="#e2e8f0"),
        width=0.5,
    ))
    
    layout = _base_layout("⏱️ Duração Média dos Jogos", height=320)
    layout["yaxis"]["title"] = "Minutos"
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return _fig_to_html(fig)


def _gen_value_analysis(s1, s2, t1, t2, odds_data):
    """
    Análise de valor: compara probabilidade implícita da odd vs dados reais.
    Só é gerado se odds_data do BetBoom estiver disponível.
    """
    if not odds_data or odds_data.get("status") != "success" or not odds_data.get("tabs"):
        return ""
    
    html = '<div class="chart-section"><div class="section-title">💰 Análise de Valor (Odds BetBoom vs Dados Reais)</div>'
    html += '<div class="charts-grid">'
    
    for tab_name, markets in odds_data["tabs"].items():
        html += f'<div class="chart-card" style="padding:16px;">'
        html += f'<h4 style="color:#a78bfa;margin:0 0 12px 0;font-size:0.95rem;">{tab_name}</h4>'
        
        for market_name, entries in markets.items():
            html += f'<div style="margin-bottom:10px;">'
            html += f'<div style="color:#e2e8f0;font-weight:600;font-size:0.85rem;margin-bottom:6px;">{market_name}</div>'
            
            for entry in entries:
                label = entry.get("label", "")
                odd_str = entry.get("odd", "")
                line = entry.get("line", "")
                
                try:
                    odd_val = float(odd_str)
                    implied_prob = 1 / odd_val * 100
                except (ValueError, ZeroDivisionError):
                    implied_prob = None
                
                # Tenta comparar com dados reais
                real_prob = None
                badge_class = "value-neutral"
                analysis_text = ""
                
                if implied_prob is not None:
                    # Vencedor
                    label_lower = label.lower() if label else ""
                    t1_lower = t1.lower()
                    t2_lower = t2.lower()
                    
                    if "vencedor" in market_name.lower() or market_name.lower().startswith("vencedor"):
                        if t1_lower in label_lower or any(w in label_lower for w in t1_lower.split()):
                            real_prob = s1["win_rate"]
                        elif t2_lower in label_lower or any(w in label_lower for w in t2_lower.split()):
                            real_prob = s2["win_rate"]
                    
                    if real_prob is not None:
                        diff = real_prob - implied_prob
                        if diff > 5:
                            badge_class = "value-good"
                            analysis_text = f"✅ VALUE! Real {real_prob:.0f}% > Implícita {implied_prob:.0f}% (+{diff:.0f}%)"
                        elif diff < -5:
                            badge_class = "value-bad"
                            analysis_text = f"❌ Sem valor. Real {real_prob:.0f}% < Implícita {implied_prob:.0f}% ({diff:.0f}%)"
                        else:
                            badge_class = "value-neutral"
                            analysis_text = f"⚖️ Justo. Real {real_prob:.0f}% ≈ Implícita {implied_prob:.0f}%"
                
                # Renderiza a entry
                line_display = f' <span style="color:#94a3b8;">({line})</span>' if line else ""
                odd_display = f'<span style="color:#fbbf24;font-weight:700;">{odd_str}</span>' if odd_str else ""
                prob_display = f' <span style="color:#94a3b8;font-size:0.8rem;">({implied_prob:.0f}%)</span>' if implied_prob else ""
                
                html += f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
                html += f'<span style="color:#cbd5e1;min-width:120px;">{label}{line_display}</span>'
                html += f'{odd_display}{prob_display}'
                if analysis_text:
                    html += f'<span class="value-badge {badge_class}" style="margin-left:auto;">{analysis_text}</span>'
                html += '</div>'
            
            html += '</div>'
        
        html += '</div>'
    
    html += '</div></div>'
    return html


# ============================================================================
# Função Principal
# ============================================================================

def generate_charts(team1, team2, odds_data=None):
    """
    Gera todos os gráficos HTML a partir dos dados Silver + BetBoom (opcional).
    
    Args:
        team1: Nome do Time 1
        team2: Nome do Time 2
        odds_data: dict do scraper BetBoom (opcional, pode ser None)
    
    Returns:
        str: HTML completo com todos os gráficos
    """
    # 1. Busca stats do banco Silver
    print(f"  📊 Consultando estatísticas de '{team1}'...")
    stats1 = _get_team_stats(team1)
    print(f"  📊 Consultando estatísticas de '{team2}'...")
    stats2 = _get_team_stats(team2)
    
    if not stats1 and not stats2:
        return f"""
        <div style="text-align:center;padding:40px;color:#f87171;">
            <h3>⚠️ Dados não encontrados</h3>
            <p>Nenhum dado histórico encontrado para '{team1}' nem '{team2}' no banco Silver.</p>
            <p style="color:#94a3b8;">Verifique se o Pipeline foi executado e se os nomes dos times estão corretos.</p>
        </div>
        """
    
    if not stats1:
        return f'<div style="text-align:center;padding:40px;color:#f87171;">⚠️ Time "{team1}" não encontrado no banco de dados.</div>'
    if not stats2:
        return f'<div style="text-align:center;padding:40px;color:#f87171;">⚠️ Time "{team2}" não encontrado no banco de dados.</div>'
    
    # 2. Monta o HTML
    html = INSIGHTS_CSS
    html += '<div class="insights-container">'
    
    # Header — usa inline styles porque Gradio remove <style> tags
    html += f'''
    <div style="text-align:center;padding:30px 20px;background:linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%);border-radius:16px;margin-bottom:24px;border:1px solid rgba(59,130,246,0.3);">
        <h2 style="margin:0 0 8px 0;font-size:1.5rem;color:#60a5fa;">📊 Insights de Apostas ao Vivo</h2>
        <div style="display:inline-flex;align-items:center;gap:12px;background:rgba(30,41,59,0.8);padding:8px 24px;border-radius:50px;border:1px solid rgba(59,130,246,0.2);">
            <span style="color:#60a5fa;font-weight:700;font-size:1.1rem;">{team1}</span>
            <span style="color:#eab308;font-weight:800;font-size:0.9rem;">VS</span>
            <span style="color:#f87171;font-weight:700;font-size:1.1rem;">{team2}</span>
        </div>
        <div style="display:flex;justify-content:center;gap:20px;margin-top:16px;">
            <div style="background:rgba(30,41,59,0.6);padding:12px 20px;border-radius:12px;border:1px solid rgba(59,130,246,0.15);text-align:center;min-width:100px;">
                <div style="font-size:1.4rem;font-weight:800;color:#60a5fa;">{stats1["total_games"]}</div>
                <div style="color:#94a3b8;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">Jogos {team1}</div>
            </div>
            <div style="background:rgba(30,41,59,0.6);padding:12px 20px;border-radius:12px;border:1px solid rgba(59,130,246,0.15);text-align:center;min-width:100px;">
                <div style="font-size:1.4rem;font-weight:800;color:#60a5fa;">{stats2["total_games"]}</div>
                <div style="color:#94a3b8;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">Jogos {team2}</div>
            </div>
            <div style="background:rgba(30,41,59,0.6);padding:12px 20px;border-radius:12px;border:1px solid rgba(59,130,246,0.15);text-align:center;min-width:100px;">
                <div style="font-size:1.4rem;font-weight:800;color:#60a5fa;">{stats1["avg_kills"]:.1f} vs {stats2["avg_kills"]:.1f}</div>
                <div style="color:#94a3b8;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">Média Kills</div>
            </div>
        </div>
    </div>
    '''
    
    # Win Rate
    html += '<div style="margin-bottom:24px;"><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;">{_gen_winrate_chart(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'
    
    # Radar
    html += '<div style="margin-bottom:24px;"><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;">{_gen_radar_chart(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'
    
    # Kills + Objetivos
    html += '<div style="margin-bottom:24px;"><div style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #3b82f6;">⚔️ Análise de Combate e Objetivos</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += f'<div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;">{_gen_kills_comparison(stats1, stats2, team1, team2)}</div>'
    html += f'<div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;">{_gen_objectives_chart(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'
    
    # First Objectives + Duração
    html += '<div style="margin-bottom:24px;"><div style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #3b82f6;">🎯 First Objectives & Tempo</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += f'<div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;">{_gen_first_objectives_chart(stats1, stats2, team1, team2)}</div>'
    html += f'<div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;">{_gen_duration_chart(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'
    
    # Forma recente
    html += '<div style="margin-bottom:24px;"><div style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #3b82f6;">📈 Forma Recente</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += _gen_recent_form(stats1, stats2, team1, team2)
    html += '</div></div>'
    
    # Análise de valor (se BetBoom disponível)
    value_html = _gen_value_analysis(stats1, stats2, team1, team2, odds_data)
    if value_html:
        html += value_html
    
    # Footer
    betboom_status = "✅ Odds BetBoom disponíveis" if (odds_data and odds_data.get("status") == "success") else "ℹ️ Análise baseada apenas em dados históricos"
    html += f'''
    <div style="text-align:center;color:#64748b;font-size:0.8rem;margin-top:20px;padding:12px;">
        Dados extraídos da camada Silver (banco local). {betboom_status}<br>
        ⚠️ Este é um projeto educacional. Aposte com responsabilidade.
    </div>
    '''
    
    html += '</div>'
    
    return html
