"""
Módulo de Geração de Gráficos — Advanced Analytics + Oracle's Elixir
Gera gráficos Plotly dinâmicos usando todos os dados históricos reais da camada Silver,
com análise estatística completa, odds ideais, textos explicativos e conceitos fundamentais de estatística.
"""

import sqlite3
import os
import statistics
from collections import Counter
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
# Helpers
# ============================================================================

def _get_db_path():
    candidates = [
        os.path.join("data", "db", "lol_datamatches.db"),
        os.path.join("..", "data", "db", "lol_datamatches.db"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]

def _base_layout(title="", height=400):
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
    import html as html_module
    raw_html = fig.to_html(
        full_html=True, include_plotlyjs="cdn",
        config={"displayModeBar": True, "scrollZoom": True, "responsive": True,
                "modeBarButtonsToRemove": ["sendDataToCloud", "editInChartStudio", "lasso2d"]},
    )
    escaped = html_module.escape(raw_html)
    height = fig.layout.height or 400
    return f'<iframe srcdoc="{escaped}" style="width:100%;height:{height + 50}px;border:none;background:transparent;" scrolling="no"></iframe>'

def _int_list(data):
    return [int(round(v)) for v in data if v is not None]

def _float_list(data):
    return [float(v) for v in data if v is not None]

def _calc_stats(data):
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

def _stats_html(st, unit=""):
    if not st:
        return ""
    u = unit
    return (
        f'<span class="stats-badge" style="background:rgba(59,130,246,0.15);color:#60a5fa;" data-tip="Média (μ): Valor central de todos os dados. Em LoL, indica a tendência de longo prazo do time.">μ={st["avg"]:.1f}{u}</span>'
        f'<span class="stats-badge" style="background:rgba(168,85,247,0.15);color:#c084fc;" data-tip="Mediana: O valor do meio quando os dados são ordenados. Menos afetada por jogos extremos (stomps ou derrotas pesadas).">Med={st["med"]:.1f}{u}</span>'
        f'<span class="stats-badge" style="background:rgba(34,197,94,0.15);color:#4ade80;" data-tip="Desvio Padrão (σ): Mede a consistência. σ baixo = time previsível, σ alto = resultados voláteis (bom para apostas de risco).">σ={st["std"]:.1f}</span>'
        f'<span class="stats-badge" style="background:rgba(234,179,8,0.12);color:#fbbf24;" data-tip="Min/Max: Os extremos históricos. Mostra o pior e o melhor desempenho do time nesta métrica.">Min={st["min"]:.0f} Max={st["max"]:.0f}</span>'
        f'<span class="stats-badge" style="background:rgba(99,102,241,0.15);color:#818cf8;" data-tip="Moda: O valor que mais se repete. Em LoL, indica o resultado \x27típico\x27 da equipe.">Moda={st["mode"]:.1f}</span>'
        f'<span class="stats-badge" style="background:rgba(236,72,153,0.12);color:#f472b6;" data-tip="Percentis 25/75: 50% dos resultados caem entre P25 e P75. É a faixa \x27normal\x27 de desempenho.">P25={st["p25"]:.1f} P75={st["p75"]:.1f}</span>'
    )

_bet_id_counter = [0]

def _odd_badge(prob):
    if not prob or prob <= 0:
        return ""
    odd = 100 / prob
    return f'<span class="odd-badge">💰 Odd ideal: {odd:.2f} (prob. {prob:.0f}%)</span>'

def _explain(text):
    return f'<div class="explain-box">📖 <b>Como ler:</b> {text}</div>'

def _risk_tier(prob):
    if prob >= 65: return ("low", "🟢 Baixo Risco")
    if prob >= 50: return ("med", "🟡 Risco Médio")
    return ("high", "🔴 Alto Risco")

def _bet_line(team, market, line, prob, data_points, explanation):
    """Gera um card de aposta com details/summary nativo (funciona sem JS)."""
    if prob is None or prob <= 0: return ""
    odd = 100 / prob
    tier, label = _risk_tier(prob)
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


# ============================================================================
# Queries no Banco Silver (Todas as Métricas)
# ============================================================================

def _build_patch_clause(patches):
    if not patches or "Todos" in patches:
        return "", []
    placeholders = ",".join(["?" for _ in patches])
    return f" AND patch IN ({placeholders})", list(patches)

def _get_team_stats(team_name, patches=None):
    db_path = _get_db_path()
    patch_clause, patch_params = _build_patch_clause(patches)
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        base_where = f"position='team' AND teamname = ?{patch_clause}"
        params = [team_name] + patch_params

        # Média e valores principais
        c.execute(f"""
            SELECT 
                COUNT(DISTINCT gameid),
                SUM(CASE WHEN result='1' THEN 1 ELSE 0 END),
                AVG(teamkills), AVG(teamdeaths),
                AVG(dragons), AVG(towers), AVG(barons), AVG(heralds), AVG(inhibitors),
                AVG(gamelength),
                AVG(CASE WHEN firstblood=1 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN firstdragon=1 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN firstbaron=1 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN firstherald=1 THEN 1.0 ELSE 0.0 END),
                AVG(kpm), AVG(ckpm),
                AVG(totalgold), AVG(earnedgold), AVG(goldspent),
                AVG(total_cs), AVG(damagetochampions), AVG(damagetakenperminute)
            FROM match_data_silver WHERE {base_where}
        """, params)

        row = c.fetchone()
        if not row or not row[0]:
            conn.close()
            return None

        stats = {
            "total_games": row[0], "wins": row[1],
            "win_rate": (row[1] / row[0] * 100) if row[0] else 0,
            "avg_kills": row[2] or 0, "avg_deaths": row[3] or 0,
            "avg_dragons": row[4] or 0, "avg_towers": row[5] or 0,
            "avg_barons": row[6] or 0, "avg_heralds": row[7] or 0, "avg_inhibitors": row[8] or 0,
            "avg_duration_s": row[9] or 0, "avg_duration_min": (row[9] or 0) / 60,
            "fb_rate": (row[10] or 0) * 100, "fd_rate": (row[11] or 0) * 100,
            "fbaron_rate": (row[12] or 0) * 100, "fherald_rate": (row[13] or 0) * 100,
            "avg_kpm": row[14] or 0, "avg_ckpm": row[15] or 0,
            "avg_totalgold": row[16] or 0, "avg_earnedgold": row[17] or 0, "avg_goldspent": row[18] or 0,
            "avg_cs": row[19] or 0, "avg_dmg_champs": row[20] or 0, "avg_dmg_taken_pm": row[21] or 0,
        }

        # Históricos para distribuições
        history_queries = {
            "kills_history": "teamkills",
            "dragons_history": "dragons",
            "towers_history": "towers",
            "barons_history": "barons",
            "heralds_history": "heralds",
            "inhibitors_history": "inhibitors",
            "kill_diff_history": "teamkills - teamdeaths",
            "ckpm_history": "ckpm",
            "kpm_history": "kpm",
            "earnedgold_pm_history": "earnedgold / (gamelength / 60.0)",  # EGPM
            "dmg_pm_history": "damagetochampions / (gamelength / 60.0)",   # DPM
        }
        for key, col in history_queries.items():
            # Proteção contra divisão por zero no SQLite gerando NULLs indesejados
            safe_col = col.replace("gamelength", "NULLIF(gamelength, 0)")
            c.execute(f"SELECT {safe_col} FROM match_data_silver WHERE {base_where} ORDER BY gameid DESC", params)
            stats[key] = [r[0] for r in c.fetchall() if r[0] is not None]

        c.execute(f"SELECT gamelength / 60.0 FROM match_data_silver WHERE {base_where} ORDER BY gameid DESC", params)
        stats["duration_history"] = [r[0] for r in c.fetchall() if r[0] is not None]

        c.execute(f"SELECT result FROM match_data_silver WHERE {base_where} ORDER BY gameid DESC LIMIT 10", params)
        stats["recent_results"] = [r[0] for r in c.fetchall() if r[0] is not None]

        conn.close()
        return stats
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar DB (team={team_name}): {e}")
        return None


# ============================================================================
# Seções Educativas (Oracle's Elixir)
# ============================================================================

def _gen_educational_sections():
    return f'''
    <div style="background:#1e293b;border-radius:12px;padding:24px;border:1px solid #334155;margin-bottom:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3);">
        <h3 style="color:#6366f1;margin:0 0 16px 0;font-size:1.2rem;display:flex;align-items:center;gap:8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
            Oracle's Elixir: Glossário & Conceitos Essenciais
        </h3>
        
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;">
            <div>
                <h4 style="color:#cbd5e1;margin:0 0 10px 0;font-size:0.95rem;">Modelagem de Probabilidades (Odds)</h4>
                <p style="color:#94a3b8;font-size:0.85rem;line-height:1.5;margin:0;">
                    Segundo o artigo <i>"What Are the Odds?"</i>, prever estatísticas não é sobre "certezas", mas sobre identificar valor.
                    A <b>Odd Ideal</b> é calculada matematicamente como <code style="background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px;">1 / (Probabilidade% / 100)</code> baseada no histórico.<br><br>
                    Se a odd recomendada for <b>1.50</b> (66% de chance) e a casa de apostas estiver oferecendo <b>1.80</b>, há uma discrepância estatística (valor na aposta).
                </p>
            </div>
            <div>
                <h4 style="color:#cbd5e1;margin:0 0 10px 0;font-size:0.95rem;">EGR (Early-Game Rating) & MLR (Mid/Late Rating)</h4>
                <p style="color:#94a3b8;font-size:0.85rem;line-height:1.5;margin:0;">
                    <i>EGR</i> estima a probabilidade de um time vencer aos 15 minutos, baseado no controle de primeiros objetivos (<b style="color:#ef4444;">FB%</b>, <b style="color:#fbbf24;">FD%</b>, <b style="color:#a855f7;">HLD%</b>) e vantagem de ouro.<br><br>
                    <i>MLR</i> mede se um time destrói estruturas (Torres, <b style="color:#eab308;">FBN%</b>, Inibidores) ou perde jogos que estava ganhando. Um time com bons Barões mas longa duração sofre para fechar o mapa.
                </p>
            </div>
            <div>
                <h4 style="color:#cbd5e1;margin:0 0 10px 0;font-size:0.95rem;">Glossário de Terminologias</h4>
                <ul style="color:#94a3b8;font-size:0.8rem;line-height:1.6;margin:0;padding-left:16px;">
                    <li><span class="glossary-term">CKPM</span>: Combined Kills Per Minute (Dita a "sangria" ou velocidade do jogo).</li>
                    <li><span class="glossary-term">FB% / FD%</span>: First Blood / First Dragon Rate (Controle inicial).</li>
                    <li><span class="glossary-term">FBN%</span>: First Baron Rate (Controle de mapa mid-late).</li>
                    <li><span class="glossary-term">EGPM</span>: Earned Gold Per Minute (Mede eficiência na fazenda/abates).</li>
                    <li><span class="glossary-term">DPM</span>: Damage Per Minute (O dano real trocado com campeões).</li>
                </ul>
            </div>
        </div>
    </div>
    '''

# ============================================================================
# Gráficos e Componentes Visuais
# ============================================================================

def _gen_winrate_chart(s1, s2, t1, t2):
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "indicator"}, {"type": "indicator"}]])
    for col, (s, t, color, bar_color) in enumerate([
        (s1, t1, "#60a5fa", "#3b82f6"), (s2, t2, "#f87171", "#ef4444")
    ], 1):
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta", value=s["win_rate"],
            number=dict(suffix="%", font=dict(size=36, color=color)),
            gauge=dict(axis=dict(range=[0, 100]), bar=dict(color=bar_color),
                       bgcolor="#1e293b", bordercolor="#334155",
                       steps=[dict(range=[0, 40], color="rgba(239,68,68,0.15)"),
                              dict(range=[40, 60], color="rgba(234,179,8,0.15)"),
                              dict(range=[60, 100], color="rgba(34,197,94,0.15)")]),
            delta=dict(reference=50, suffix="%"),
        ), row=1, col=col)
    fig.update_layout(**_base_layout("🏆 Win Rate", height=300))
    fig.update_layout(annotations=[
        dict(text=t1, x=0.2, y=1.12, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="#60a5fa")),
        dict(text=t2, x=0.8, y=1.12, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="#f87171")),
    ])
    return _fig_to_html(fig)

def _gen_recent_form(s1, s2, t1, t2):
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">📈 Forma Recente (últimos 10 jogos)</h3>'
    for team_name, stats, color in [(t1, s1, "#3b82f6"), (t2, s2, "#ef4444")]:
        results = stats.get("recent_results", [])
        recent_wr = sum(1 for r in results if r == '1') / len(results) * 100 if results else 0
        html += f'<div style="margin-bottom:12px;">'
        html += f'<span style="color:{color};font-weight:700;">{team_name}</span>'
        html += f'<span style="color:#94a3b8;margin-left:8px;font-size:0.85rem;">(WR recente: {recent_wr:.0f}%)</span>'
        html += '<div style="display:flex;gap:4px;margin-top:6px;">'
        for r in results:
            if r == '1':
                html += '<div style="width:32px;height:32px;border-radius:6px;background:rgba(34,197,94,0.3);border:1px solid #22c55e;display:flex;align-items:center;justify-content:center;font-weight:700;color:#4ade80;font-size:0.8rem;">W</div>'
            else:
                html += '<div style="width:32px;height:32px;border-radius:6px;background:rgba(239,68,68,0.2);border:1px solid #ef4444;display:flex;align-items:center;justify-content:center;font-weight:700;color:#f87171;font-size:0.8rem;">L</div>'
        html += '</div></div>'
    html += _explain("Sequências longas de vitórias indicam momento favorável emocionalmente (<i>Momentum</i>).")
    html += '</div>'
    return html

def _gen_bloodiness_pace(s1, s2, t1, t2):
    """Gráfico de Ritmo de Jogo: CKPM e KPM"""
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">🩸 Pace & Bloodiness (CKPM e KPM)</h3>'

    for name, key, is_combined in [("CKPM (Combined Kills/Min)", "ckpm_history", True), ("KPM (Team Kills/Min)", "kpm_history", False)]:
        html += f'<div style="margin-bottom:16px;">'
        html += f'<div style="color:#e2e8f0;font-weight:600;font-size:0.9rem;margin-bottom:8px;">{name}</div>'
        
        for stats, team, color in [(s1, t1, "#60a5fa" if not is_combined else "#c084fc"), 
                                   (s2, t2, "#f87171" if not is_combined else "#e879f9")]:
            data = _float_list(stats.get(key, []))
            if not data: continue
            avg_val = sum(data)/len(data)
            
            # Barras visuais simples para contexto
            max_scale = 1.0 if is_combined else 0.5
            width_pct = min(100, (avg_val / max_scale) * 100)
            
            html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            html += f'<span style="color:{color};font-weight:700;min-width:120px;font-size:0.85rem;">{team}</span>'
            html += f'<div style="flex:1;background:#1e293b;border-radius:4px;height:20px;overflow:hidden;">'
            html += f'<div style="width:{width_pct:.0f}%;height:100%;background:{color};border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:0.75rem;font-weight:700;color:white;">{avg_val:.2f} abates/min</div></div>'
            html += '</div>'
        html += '</div>'

    html += _explain("<b>CKPM</b> indica o ritmo global da partida. CKPM > 0.8 indicam jogos 'sangrentos', cheios de lutas (favorável para Overs de Kills). <b>KPM</b> mede a letalidade bruta de apenas um time.")
    html += '</div>'
    return html

def _gen_economy_cards(s1, s2, t1, t2):
    """Métricas de Economia: EGPM e DPM (As verdadeiras medidas de sucesso)"""
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">💰 Economia & Dano (The Advanced Stats Problem)</h3>'
    
    metrics = [
        ("EGPM (Earned Gold/Min)", "earnedgold_pm_history", "Ouro farmado/min (ignora ouro inicial), define o potencial de compra de itens. Alta EGPM = farm massivo ou farm de tropas."),
        ("DPM (Damage/Min)", "dmg_pm_history", "Dano a campeões por minuto. Matar é importante, mas espalhar dano pavimenta as teamfights."),
    ]
    
    for title, key, exp in metrics:
        html += f'<div style="margin-bottom:16px;">'
        html += f'<div style="color:#fbbf24;font-weight:600;font-size:0.9rem;margin-bottom:8px;">{title}</div>'
        
        for stats, team, color in [(s1, t1, "#60a5fa"), (s2, t2, "#f87171")]:
            data = _float_list(stats.get(key, []))
            if not data: continue
            st = _calc_stats(data)
            
            html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            html += f'<span style="color:{color};font-weight:700;min-width:120px;font-size:0.85rem;">{team}</span>'
            html += f'<span style="color:#e2e8f0;font-size:0.9rem;">{st["avg"]:.0f}</span> '
            html += f'<span style="color:#64748b;font-size:0.75rem;">(Max: {st["max"]:.0f} / Min: {st["min"]:.0f})</span>'
            html += '</div>'
        
        html += f'<div style="color:#94a3b8;font-size:0.75rem;border-left:2px solid #334155;padding-left:8px;margin-top:4px;"><i>{exp}</i></div>'
        html += '</div>'

    html += _explain("Segundo o artigo <i>LoL\'s Advanced Stats Problem</i>, olhar apenas para KDA é uma armadilha. A verdadeira pressão do jogo provém de <b>Ouro Ganho (EGPM)</b> e <b>Dano Gerado (DPM)</b>.")
    html += '</div>'
    return html

def _gen_first_objectives_egr(s1, s2, t1, t2):
    """Early Game Rating Proxy (First Blood, Dragon, Herald, Tower se houvesse)"""
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">⚡ Early-Game Rating (EGR) Proxy — Primeiros Objetivos</h3>'
    
    fb1, fb2 = s1["fb_rate"], s2["fb_rate"]
    fd1, fd2 = s1["fd_rate"], s2["fd_rate"]
    fh1, fh2 = s1["fherald_rate"], s2["fherald_rate"]
    
    categories = [("First Blood (FB%)", fb1, fb2), ("First Dragon (FD%)", fd1, fd2), ("First Herald (HLD%)", fh1, fh2)]
    
    for title, v1, v2 in categories:
        html += f'<div style="margin-bottom:12px;">'
        html += f'<div style="color:#cbd5e1;font-weight:600;font-size:0.85rem;margin-bottom:4px;">{title}</div>'
        # T1 Bar
        html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
        html += f'<span style="color:#60a5fa;font-weight:700;min-width:40px;text-align:right;font-size:0.8rem;">{v1:.0f}%</span>'
        html += f'<div style="flex:1;background:#1e293b;border-radius:4px;height:12px;overflow:hidden;">'
        html += f'<div style="width:{v1:.0f}%;height:100%;background:#3b82f6;border-radius:4px;"></div></div></div>'
        # T2 Bar
        html += f'<div style="display:flex;align-items:center;gap:8px;">'
        html += f'<span style="color:#f87171;font-weight:700;min-width:40px;text-align:right;font-size:0.8rem;">{v2:.0f}%</span>'
        html += f'<div style="flex:1;background:#1e293b;border-radius:4px;height:12px;overflow:hidden;">'
        html += f'<div style="width:{v2:.0f}%;height:100%;background:#ef4444;border-radius:4px;"></div></div></div>'
        html += '</div>'

    html += _explain("O modelo de <b>EGR</b> do Oracle's Elixir demonstra que o time que conquista esses prêmios iniciais cria uma vantagem de ouro aos 15 minutos que se converte numa <b>Probabilidade de Vitória (Odds)</b> gigantesca. Observe a discrepância nas barras.")
    html += '</div>'
    return html

def _gen_mlr_proxy(s1, s2, t1, t2):
    """Mid/Late Rating Proxy (Barons, Inhibitors, Towers)"""
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">🏰 Mid/Late Rating (MLR) Proxy — Controle de Mapa</h3>'
    
    html += '''<table style="width:100%;border-collapse:collapse;font-size:0.85rem;text-align:center;">
        <tr style="color:#94a3b8;border-bottom:1px solid #334155;">
            <th style="padding:8px;text-align:left;">Time</th>
            <th>First Baron (FBN%)</th>
            <th>Média Barões</th>
            <th>Média Inibidores</th>
            <th>Média Torres</th>
        </tr>'''
    
    for stats, team, color in [(s1, t1, "#60a5fa"), (s2, t2, "#f87171")]:
        html += f'<tr style="color:#e2e8f0;border-bottom:1px solid rgba(51,65,85,0.5);">'
        html += f'<td style="padding:8px;text-align:left;color:{color};font-weight:700;">{team}</td>'
        html += f'<td>{stats["fbaron_rate"]:.0f}%</td>'
        html += f'<td>{stats["avg_barons"]:.1f}</td>'
        html += f'<td>{stats["avg_inhibitors"]:.2f}</td>'
        html += f'<td>{stats["avg_towers"]:.1f}</td>'
        html += '</tr>'
    
    html += '</table>'
    html += '<div style="margin-top:16px;"></div>'
    html += _explain("O modelo <b>MLR</b> mostra como o time fecha o jogo no Mid-Late Game. Ter Barões sem destruir Inibidores e Torres indica um time passivo que não consegue <i>snowballar</i> sua vantagem. Excelente para apostas no <b>Handicap de Torres</b>.")
    html += '</div>'
    return html


# Gráficos Dinâmicos Plotly

def _gen_total_abates(s1, s2, t1, t2):
    k1 = _int_list(s1.get("kills_history", []))
    k2 = _int_list(s2.get("kills_history", []))
    min_len = min(len(k1), len(k2))
    if min_len == 0: return ""
    total = [k1[i] + k2[i] for i in range(min_len)]
    st = _calc_stats(total)
    counts = Counter(total)
    x_vals = sorted(counts.keys())
    y_vals = [counts[v] for v in x_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_vals, y=y_vals, marker_color="#a78bfa", marker_line_color="#c4b5fd", marker_line_width=1, text=[str(c) for c in y_vals], textposition="outside"))
    fig.add_vline(x=st["avg"], line=dict(color="#a78bfa", width=2.5, dash="dash"))
    layout = _base_layout(f"⚔️ Total de Abates na Partida — {t1} vs {t2}", height=380)
    layout["xaxis"]["title"] = "Total de Kills no Jogo"
    layout["yaxis"]["title"] = "Nº de Jogos"
    fig.update_layout(**layout)

    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas sugeridas (Total Kills):</b><br>'
    for lv in [st["avg"] - 5, st["avg"] - 2.5, st["avg"], st["avg"] + 2.5, st["avg"] + 5]:
        line_v = round(lv * 2) / 2
        prob_over = sum(1 for v in total if v > line_v) / len(total) * 100
        prob_under = 100 - prob_over
        bets += _bet_line(f"{t1}+{t2}", "Over", f"{line_v:.1f} kills", prob_over, len(total),
            f"Em {sum(1 for v in total if v > line_v)} de {len(total)} jogos o total de kills foi > {line_v:.1f}. "
            f"Média histórica: {st['avg']:.1f}, Mediana: {st['med']:.1f}, Desvio Padrão: {st['std']:.1f}. "
            f"{'Alta confiança: a linha está abaixo da média.' if line_v < st['avg'] else 'Linha acima da média: depende de jogos sangrentos (alto CKPM).'}")
        bets += _bet_line(f"{t1}+{t2}", "Under", f"{line_v:.1f} kills", prob_under, len(total),
            f"Em {sum(1 for v in total if v <= line_v)} de {len(total)} jogos o total de kills foi ≤ {line_v:.1f}. "
            f"{'Conservador: linha acima da média favorece Under.' if line_v > st['avg'] else 'Arriscado: linha abaixo da média desfavorece Under.'}")
        bets += '<br>'
    bets += '</div>'

    return (_fig_to_html(fig) + f'<div style="margin-top:8px;">{_stats_html(st)}</div>' + bets
            + _explain("A distribuição do <b>total de kills na partida</b> (soma). É guiada pela métrica global <b>CKPM</b> detalhada acima. Em jogos com times sanguinários, a cauda longa no gráfico encosta nos 40-50 abates."))


def _gen_kills_por_time(s1, s2, t1, t2):
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    stats_htmls = []
    for col, (stats, team, bar_color, line_color) in enumerate([(s1, t1, "#3b82f6", "#60a5fa"), (s2, t2, "#ef4444", "#f87171")], 1):
        raw = _int_list(stats.get("kills_history", []))
        if not raw: continue
        st = _calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_color, marker_line_color=line_color, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_color, width=2.5, dash="dash"), row=1, col=col)
        avg_line = round(st["avg"] * 2) / 2
        pct_over = sum(1 for v in raw if v > avg_line) / len(raw) * 100
        stats_htmls.append(f'<div style="margin-top:4px;"><span style="color:{line_color};font-weight:700;">{team}:</span> {_stats_html(st)} {_odd_badge(pct_over)} <b>Over {avg_line:.1f} kills</b></div>')

    layout = _base_layout("🎯 Distribuição de Kills Individuais", height=420)
    fig.update_layout(**layout)
    return (_fig_to_html(fig) + "".join(stats_htmls)
            + _explain("A <b>Odd ideal</b> exibida refere-se à entrada <b>Over X.X kills</b> (arredondamento da média). Se o time puxar mais que a média histórica, a linha é coberta. Kills por time medem a pressão terminal, mas times com alta kill rate sem EGR alto podem estar apenas sendo engajados frequentemente."))

def _gen_handicap(s1, s2, t1, t2):
    fig = go.Figure()
    odds_html = ""
    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas de Handicap sugeridas:</b><br>'
    for stats, team, bar_col, line_col in [(s1, t1, "rgba(59,130,246,0.7)", "#60a5fa"), (s2, t2, "rgba(239,68,68,0.7)", "#f87171")]:
        data = [int(round(v)) for v in stats.get("kill_diff_history", []) if v is not None]
        if not data: continue
        st = _calc_stats(data)
        counts = Counter(data)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=f"{team} (μ={st['avg']:+.1f})", marker_color=bar_col, marker_line_color=line_col, marker_line_width=1))
        pct_pos = sum(1 for v in data if v > 0) / len(data) * 100
        odds_html += f'<div style="margin-top:4px;"><span style="color:{line_col};font-weight:700;">{team}:</span> {_stats_html(st)} {_odd_badge(pct_pos)} <b>Handicap 0 (Positivo > 0 kills)</b></div>'

        for hc_line in [-7.5, -5.5, -3.5, -1.5, 0, 1.5, 3.5, 5.5, 7.5]:
            prob = sum(1 for v in data if v > hc_line) / len(data) * 100
            sign = "+" if hc_line >= 0 else ""
            bets += _bet_line(team, "Handicap", f"{sign}{hc_line:.1f} kills", prob, len(data),
                f"Em {sum(1 for v in data if v > hc_line)} de {len(data)} jogos, {team} teve diff > {hc_line:+.1f}. "
                f"Média de handicap: {st['avg']:+.1f}, Mediana: {st['med']:+.1f}, Desvio Padrão: {st['std']:.1f}. "
                f"{'Linha conservadora abaixo da média — alta cobertura.' if hc_line < st['avg'] else 'Linha agressiva acima da média — precisa de domínio claro.'}")
        bets += '<br>'
    bets += '</div>'

    # Texto educativo sobre o que é Handicap
    handicap_explain = (
        '<div class="explain-box" style="margin-top:14px;border-left-color:#eab308;">'
        '🎮 <b>O que é o Handicap de Kills?</b><br>'
        'O Handicap mede a <b>diferença entre kills do time e kills sofridas</b> (teamkills - teamdeaths). '
        'Na prática, funciona assim:<br><br>'
        '<b>Exemplo 1:</b> Se você aposta em <b>FURIA Handicap -3.5</b>, a FURIA precisa vencer a partida com pelo '
        'menos <b>4 kills a mais</b> que o adversário (ex: 15×11 = diff +4 ✔️, 12×10 = diff +2 ❌).<br>'
        '<b>Exemplo 2:</b> Se você aposta em <b>Sentinels Handicap +5.5</b>, os Sentinels podem até <b>perder por '
        'até 5 kills de diferença</b> e sua aposta cobre (ex: 8×12 = diff -4 ✔️, 5×12 = diff -7 ❌).<br><br>'
        '<b>Handicap negativo (-)</b> = time precisa dominar. <b>Handicap positivo (+)</b> = time recebe "vantagem" virtual. '
        'Quanto mais extrema a linha, maior a odd e o risco.'
        '</div>'
    )

    fig.add_vline(x=0, line=dict(color="#94a3b8", width=1.5))
    layout = _base_layout("📊 Handicap de Kills (Kill Diff)", height=380)
    layout["barmode"] = "overlay"
    layout["xaxis"]["title"] = "Diferença de Kills (positivo = dominou)"
    fig.update_layout(**layout)
    return (_fig_to_html(fig) + odds_html + handicap_explain + bets
            + _explain("A <b>Odd ideal</b> mostrada acima refere-se à entrada <b>Handicap 0</b> (mais kills que mortes). Clique nas entradas para ver o detalhamento individual."))

def _gen_duracao(s1, s2, t1, t2):
    all_dur = [v for v in s1.get("duration_history", []) + s2.get("duration_history", []) if v]
    if not all_dur: return ""
    st = _calc_stats(all_dur)
    fig = go.Figure()
    for stats, team, color in [(s1, t1, "rgba(59,130,246,0.55)"), (s2, t2, "rgba(239,68,68,0.55)")]:
        data = [v for v in stats.get("duration_history", []) if v]
        if data: fig.add_trace(go.Histogram(x=data, name=team, marker_color=color, opacity=0.7, xbins=dict(size=2)))
    fig.add_vline(x=st["avg"], line=dict(color="#22c55e", width=2.5, dash="dash"))
    layout = _base_layout("⏱️ Duração do Mapa (Pace Control)", height=380)
    layout["barmode"] = "overlay"
    layout["xaxis"]["title"] = "Duração (minutos)"
    fig.update_layout(**layout)

    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas de Duração sugeridas:</b><br>'
    for lv in [25.5, 28.5, 31.5, 34.5, 37.5]:
        p_over = sum(1 for v in all_dur if v > lv) / len(all_dur) * 100
        p_under = 100 - p_over
        bets += _bet_line(f"{t1}+{t2}", "Over", f"{lv}min", p_over, len(all_dur),
            f"Em {sum(1 for v in all_dur if v > lv)} de {len(all_dur)} jogos a duração excedeu {lv}min. "
            f"Média: {st['avg']:.1f}min, Mediana: {st['med']:.1f}min. "
            f"{'Linha conservadora.' if lv < st['avg'] else 'Linha agressiva — requer jogos longos.'}")
        bets += _bet_line(f"{t1}+{t2}", "Under", f"{lv}min", p_under, len(all_dur),
            f"Em {sum(1 for v in all_dur if v <= lv)} de {len(all_dur)} jogos a duração foi ≤ {lv}min. "
            f"{'Favorável: linha acima da média.' if lv > st['avg'] else 'Arriscado: linha abaixo da média.'}")
        bets += '<br>'
    bets += '</div>'

    return (_fig_to_html(fig) + f'<div style="margin-top:8px;">{_stats_html(st, "min")}</div>' + bets
            + _explain("A <b>Duração (AGT - Avg Game Time)</b> reflete se os times controlam o pace. Um time de EGR baixo e AGT alto joga na defensiva pelas torres e falha nas chamadas de Barão."))


# ============================================================================
# Recomendações Automáticas de Apostas (Value Finding)
# ============================================================================

def _gen_betting_recommendations(s1, s2, t1, t2):
    """Expected Value Finder completo — gera entradas para TODOS os tiers de risco usando
    análise cruzada de múltiplas estatísticas (Oracle's Elixir methodology)."""
    html = ""

    def rp(data, cond):
        v = [x for x in data if x is not None]
        return (sum(1 for x in v if cond(x)) / len(v) * 100, len(v)) if v else (None, 0)

    # Separar por categoria para visual
    categories = []

    for stats, team, tcolor in [(s1, t1, "#60a5fa"), (s2, t2, "#f87171")]:
        kills = stats.get("kills_history", [])
        kd = stats.get("kill_diff_history", [])
        drag = stats.get("dragons_history", [])
        tow = stats.get("towers_history", [])
        bar = stats.get("barons_history", [])
        dur = stats.get("duration_history", [])
        n = stats["total_games"]
        avg_k = stats["avg_kills"]
        wr = stats["win_rate"]
        fb = stats["fb_rate"]
        fd = stats["fd_rate"]
        fh = stats["fherald_rate"]
        fbn = stats["fbaron_rate"]
        egpm_data = stats.get("earnedgold_pm_history", [])
        dpm_data = stats.get("dmg_pm_history", [])

        entries = []

        # --- 1. VENCEDOR (Match Winner) ---
        egr_score = (fb + fd + fh) / 3  # Early Game Rating proxy
        mlr_indicators = (stats["avg_barons"] + stats["avg_inhibitors"] + stats["avg_towers"] / 5) / 3
        combined_score = wr * 0.5 + egr_score * 0.3 + min(mlr_indicators * 20, 100) * 0.2
        entries.append(_bet_line(team, "Vencedor (ML)", "Moneyline", wr, n,
            f"Win Rate histórico: {wr:.1f}%. "
            f"EGR Proxy Score (FB%+FD%+HLD%)/3: {egr_score:.0f}%. "
            f"MLR Proxy (Barões+Inibs+Torres): {mlr_indicators:.2f}. "
            f"Score Combinado (50% WR + 30% EGR + 20% MLR): {combined_score:.0f}%. "
            f"Segundo o artigo 'What Are the Odds?', a probabilidade real de vitória "
            f"é melhor estimada combinando múltiplas métricas do que usando Win Rate isolado. "
            f"Se o time domina o Early (EGR alto) E fecha jogos (MLR alto), o WR tende a subestimar a força real."))

        # --- 2. KILLS POR TIME (Over/Under em múltiplas linhas) ---
        for line in [round((avg_k - 4) * 2) / 2, round((avg_k - 2) * 2) / 2, round(avg_k * 2) / 2, round((avg_k + 2) * 2) / 2, round((avg_k + 4) * 2) / 2]:
            prob_o, cnt = rp(kills, lambda v, l=line: v > l)
            if prob_o is not None and prob_o > 5:
                entries.append(_bet_line(team, "Over Kills", f"{line:.1f}", prob_o, cnt,
                    f"Em {sum(1 for v in kills if v is not None and v > line)} de {cnt} jogos, {team} fez > {line:.1f} kills. "
                    f"Média: {avg_k:.1f}, KPM médio: {stats['avg_kpm']:.2f}, CKPM: {stats['avg_ckpm']:.2f}. "
                    f"EGPM ({_float_list(egpm_data) and sum(_float_list(egpm_data))/len(_float_list(egpm_data)) or 0:.0f}/min) e "
                    f"DPM ({_float_list(dpm_data) and sum(_float_list(dpm_data))/len(_float_list(dpm_data)) or 0:.0f}/min) "
                    f"indicam {'pressão ofensiva alta' if stats['avg_kpm'] > 0.3 else 'estilo mais passivo'}. "
                    f"{'Alta CKPM sugere jogos sangrentos — favorável para Overs.' if stats['avg_ckpm'] > 0.7 else 'CKPM moderada/baixa — Overs agressivos são arriscados.'}"))

        # --- 3. HANDICAP DE KILLS (múltiplas linhas) ---
        if kd:
            st_kd = _calc_stats(kd)
            for hc in [-5.5, -3.5, -1.5, 0, 1.5, 3.5, 5.5]:
                prob_hc, cnt = rp(kd, lambda v, h=hc: v > h)
                if prob_hc is not None and prob_hc > 5:
                    sign = "+" if hc >= 0 else ""
                    entries.append(_bet_line(team, "Handicap", f"{sign}{hc:.1f} kills", prob_hc, cnt,
                        f"Em {sum(1 for v in kd if v is not None and v > hc)} de {cnt} jogos, {team} teve diff > {hc:+.1f}. "
                        f"Média de handicap: {st_kd['avg']:+.1f}, σ: {st_kd['std']:.1f}. "
                        f"O artigo 'Significant Statistics' mostra que a diferença de kills está diretamente "
                        f"ligada ao Gold Difference — cada kill vale ~300-450 Gold dependendo do shutdown. "
                        f"{'Linha conservadora (negativa) — protege contra jogos ruins.' if hc < 0 else 'Linha agressiva — precisa de domínio claro no Early+Mid Game.'}"))

        # --- 4. DRAGÕES ---
        if drag:
            for dl in [2.5, 3.5, 4.5]:
                prob_d, cnt = rp(drag, lambda v, l=dl: v > l)
                if prob_d is not None and prob_d > 5:
                    entries.append(_bet_line(team, "Over Dragões", f"{dl}", prob_d, cnt,
                        f"Em {sum(1 for v in drag if v is not None and v > dl)} de {cnt} jogos, {team} pegou > {dl} dragões. "
                        f"FD% (First Dragon): {fd:.0f}%. Média: {stats['avg_dragons']:.1f}. "
                        f"Times com alta FD% controlam a rotação bot-side e acumulam dragões naturalmente. "
                        f"{'Dragon Soul exige 4 dragões — Over 3.5 é favorável para times com FD% > 55%.' if fd > 55 else 'FD% abaixo de 55% torna Over 3.5 arriscado.'}"))

        # --- 5. TORRES ---
        if tow:
            for tl in [5.5, 7.5, 9.5]:
                prob_t, cnt = rp(tow, lambda v, l=tl: v > l)
                if prob_t is not None and prob_t > 5:
                    entries.append(_bet_line(team, "Over Torres", f"{tl}", prob_t, cnt,
                        f"Em {sum(1 for v in tow if v is not None and v > tl)} de {cnt} jogos, {team} destruiu > {tl} torres. "
                        f"Média: {stats['avg_towers']:.1f}, Inibidores: {stats['avg_inhibitors']:.2f}. "
                        f"O MLR (Mid/Late Rating) mostra que times que convertem Barões em torres têm "
                        f"maior eficiência de fechamento. "
                        f"{'Alta média de torres suporta Overs agressivos.' if stats['avg_towers'] > 6 else 'Média de torres moderada — overlines altas são arriscadas.'}"))

        # --- 6. BARÕES ---
        if bar:
            for bl in [0.5, 1.5]:
                prob_b, cnt = rp(bar, lambda v, l=bl: v > l)
                if prob_b is not None and prob_b > 5:
                    entries.append(_bet_line(team, "Over Barões", f"{bl}", prob_b, cnt,
                        f"Em {sum(1 for v in bar if v is not None and v > bl)} de {cnt} jogos, {team} pegou > {bl} barões. "
                        f"FBN% (First Baron): {fbn:.0f}%, Média: {stats['avg_barons']:.1f}. "
                        f"Barões são o principal indicador do MLR — times que controlam o Baron Pit "
                        f"ditam o ritmo do mid-late game."))

        # --- 7. FIRST BLOOD ---
        entries.append(_bet_line(team, "First Blood", "Sim", fb, n,
            f"FB% histórico de {team}: {fb:.0f}% em {n} jogos. "
            f"O EGR (Early-Game Rating) é parcialmente determinado pelo First Blood, "
            f"que gera ~400g de vantagem imediata e controle de lane priority. "
            f"{'Time agressivo com alta taxa de FB.' if fb > 55 else 'FB% equilibrado — mercado volátil.'}"
            f" EGPM médio: {_float_list(egpm_data) and sum(_float_list(egpm_data))/len(_float_list(egpm_data)) or 0:.0f}/min."))

        # --- 8. FIRST DRAGON ---
        entries.append(_bet_line(team, "First Dragon", "Sim", fd, n,
            f"FD% de {team}: {fd:.0f}% em {n} jogos. "
            f"O controle do primeiro dragão indica rotação bot-side e visão do rio. "
            f"FD% > 55% combinada com FB% > 50% cria um EGR dominante."))

        # --- 9. DURAÇÃO ---
        if dur:
            for dl in [28.5, 31.5, 34.5]:
                prob_do, cnt = rp(dur, lambda v, l=dl: v > l)
                if prob_do is not None and prob_do > 5:
                    entries.append(_bet_line(team, "Over Duração", f"{dl}min", prob_do, cnt,
                        f"Em {sum(1 for v in dur if v is not None and v > dl)} de {cnt} jogos de {team}, a duração excedeu {dl}min. "
                        f"AGT (Avg Game Time): {stats['avg_duration_min']:.1f}min. "
                        f"{'Time de jogo longo — favorável para Overs de duração.' if stats['avg_duration_min'] > 32 else 'Time encerra jogos rápido — Under é favorável.'}"))

        if entries:
            categories.append((team, tcolor, entries))

    if not categories:
        return '<div style="background:#1e293b;border-radius:12px;padding:20px;border:1px solid #334155;color:#94a3b8;text-align:center;">📭 Nenhum dado disponível para gerar recomendações.</div>'

    # Função para extrair probabilidade de uma entrada para ordenação
    import re
    def _extract_prob(entry_html):
        m = re.search(r'\((\d+)%\)', entry_html)
        return int(m.group(1)) if m else 0

    # Montar HTML por time com tabs de risco
    for team, tcolor, entries in categories:
        html += f'<div style="background:#1e293b;border-radius:12px;padding:20px;border:1px solid #334155;margin-bottom:16px;">'
        html += f'<h3 style="color:{tcolor};margin:0 0 12px 0;font-size:1.1rem;">{team} — Todas as Entradas</h3>'
        html += f'<div style="color:#94a3b8;font-size:0.78rem;margin-bottom:12px;">Clique em qualquer entrada para ver o detalhamento completo do cálculo e a explicação do risco.</div>'

        # Separar por risco e ordenar por probabilidade (maior primeiro)
        low_entries = sorted([e for e in entries if '🟢' in e], key=_extract_prob, reverse=True)
        med_entries = sorted([e for e in entries if '🟡' in e], key=_extract_prob, reverse=True)
        high_entries = sorted([e for e in entries if '🔴' in e], key=_extract_prob, reverse=True)

        if low_entries:
            html += '<div style="margin-bottom:12px;"><div style="color:#4ade80;font-weight:700;font-size:0.9rem;margin-bottom:6px;">🟢 Baixo Risco (Prob. ≥ 65%) — Ordenado por probabilidade</div>'
            html += "".join(low_entries) + '</div>'
        if med_entries:
            html += '<div style="margin-bottom:12px;"><div style="color:#fbbf24;font-weight:700;font-size:0.9rem;margin-bottom:6px;">🟡 Risco Médio (Prob. 50-64%) — Ordenado por probabilidade</div>'
            html += "".join(med_entries) + '</div>'
        if high_entries:
            html += '<div style="margin-bottom:12px;"><div style="color:#f87171;font-weight:700;font-size:0.9rem;margin-bottom:6px;">🔴 Alto Risco (Prob. < 50%) — Odds Altas, ordenado por probabilidade</div>'
            html += "".join(high_entries) + '</div>'

        html += '</div>'

    return html


# ============================================================================
# Core Generation
# ============================================================================

def generate_charts(team1, team2, patches=None, odds_data=None):
    stats1 = _get_team_stats(team1, patches)
    stats2 = _get_team_stats(team2, patches)

    if not stats1 or not stats2:
        return f"<div style='text-align:center;padding:40px;color:#f87171;'><h3>⚠️ Dados insuficientes</h3></div>"

    patch_label = ", ".join(patches) if patches and "Todos" not in patches else "Todos os patches"
    CARD = 'style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;"'
    SECTION = 'style="margin-bottom:24px;"'
    TITLE = 'style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #3b82f6;"'
    TITLE2 = 'style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #a78bfa;"'
    TITLE3 = 'style="color:#eab308;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #eab308;"'

    html = INSIGHTS_CSS + '<div class="insights-container">'

    html += f'''
    <div style="text-align:center;padding:30px 20px;background:linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%);border-radius:16px;margin-bottom:24px;border:1px solid rgba(59,130,246,0.3);">
        <h2 style="margin:0 0 8px 0;font-size:1.5rem;color:#60a5fa;">📊 Advanced Analytics — Powered by Oracle's Elixir</h2>
        <div style="display:inline-flex;align-items:center;gap:12px;background:rgba(30,41,59,0.8);padding:8px 24px;border-radius:50px;border:1px solid rgba(59,130,246,0.2);">
            <span style="color:#60a5fa;font-weight:700;font-size:1.1rem;">{team1}</span>
            <span style="color:#eab308;font-weight:800;font-size:0.9rem;">VS</span>
            <span style="color:#f87171;font-weight:700;font-size:1.1rem;">{team2}</span>
        </div>
        <div style="color:#94a3b8;font-size:0.8rem;margin-top:10px;">📅 Filtro: {patch_label} | Data Pool: {stats1["total_games"]} jogos ({team1}) / {stats2["total_games"]} ({team2})</div>
    </div>
    '''

    # Glossário
    html += _gen_educational_sections()

    # Modelos Oracle's Elixir (EGR e MLR)
    html += f'<div {SECTION}><div {TITLE3}>🧠 Meta-Modelos Estruturais (EGR e MLR)</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += _gen_first_objectives_egr(stats1, stats2, team1, team2)
    html += _gen_mlr_proxy(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Economia, Dano e Sangria (Oracle's Stats problem)
    html += f'<div {SECTION}><div {TITLE3}>💥 Advanced Pacing & Economy Context</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += _gen_economy_cards(stats1, stats2, team1, team2)
    html += _gen_bloodiness_pace(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Clássicos do Preditor
    html += f'<div {SECTION}><div {TITLE}>🏆 Win Rate & Momentum</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{_gen_winrate_chart(stats1, stats2, team1, team2)}</div>'
    html += _gen_recent_form(stats1, stats2, team1, team2)
    html += '</div></div>'

    html += f'<div {SECTION}><div {TITLE2}>⚔️ Distribuições de Abates (Combate Extremo)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{_gen_total_abates(stats1, stats2, team1, team2)}</div>'
    html += f'<div {CARD}>{_gen_kills_por_time(stats1, stats2, team1, team2)}</div>'
    html += f'<div {CARD}>{_gen_handicap(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'

    html += f'<div {SECTION}><div {TITLE2}>⏱ Duração do Jogo (AGT)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{_gen_duracao(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'

    html += f'''
    <div style="text-align:center;padding:20px;margin:30px 0 24px 0;background:linear-gradient(135deg,#052e16 0%,#14532d 50%,#052e16 100%);border-radius:16px;border:1px solid rgba(34,197,94,0.3);">
        <h2 style="margin:0;font-size:1.3rem;color:#4ade80;">🎯 Expected Value Finder (Odd Mining)</h2>
        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:0.85rem;">Algoritmo de varredura buscando Edges Estatísticos baseados nos Modelos do Elixir</p>
    </div>
    '''
    html += f'<div {SECTION}>{_gen_betting_recommendations(stats1, stats2, team1, team2)}</div>'

    html += f'<div style="text-align:center;color:#64748b;font-size:0.75rem;margin-top:20px;padding:12px;">Camada Silver Analytics | Desenvolvido com Metodologia do Oracle\'s Elixir</div></div>'
    return html
