"""
charts/chart_generators.py — Strategy Pattern: cada gráfico é uma função independente.
Todas as funções recebem (s1, s2, t1, t2) e retornam HTML string.
"""

from collections import Counter
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .html_helpers import (
    base_layout, fig_to_html, int_list, float_list,
    calc_stats, stats_html, odd_badge, explain, bet_line,
)


# ============================================================================
# Win Rate & Momentum
# ============================================================================

def gen_winrate_chart(s1, s2, t1, t2):
    """Gauge duplo de Win Rate."""
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
    fig.update_layout(**base_layout("🏆 Win Rate", height=300))
    fig.update_layout(annotations=[
        dict(text=t1, x=0.2, y=1.12, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="#60a5fa")),
        dict(text=t2, x=0.8, y=1.12, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="#f87171")),
    ])
    return fig_to_html(fig)


def gen_recent_form(s1, s2, t1, t2):
    """Forma recente (últimos 10 jogos) em bloquinhos W/L."""
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
    html += explain("Sequências longas de vitórias indicam momento favorável emocionalmente (<i>Momentum</i>).")
    html += '</div>'
    return html


# ============================================================================
# Pacing & Economy
# ============================================================================

def gen_bloodiness_pace(s1, s2, t1, t2):
    """Gráfico de Ritmo de Jogo: CKPM e KPM."""
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">🩸 Pace & Bloodiness (CKPM e KPM)</h3>'

    for name, key, is_combined in [("CKPM (Combined Kills/Min)", "ckpm_history", True), ("KPM (Team Kills/Min)", "kpm_history", False)]:
        html += f'<div style="margin-bottom:16px;">'
        html += f'<div style="color:#e2e8f0;font-weight:600;font-size:0.9rem;margin-bottom:8px;">{name}</div>'
        for stats, team, color in [(s1, t1, "#60a5fa" if not is_combined else "#c084fc"),
                                   (s2, t2, "#f87171" if not is_combined else "#e879f9")]:
            data = float_list(stats.get(key, []))
            if not data:
                continue
            avg_val = sum(data) / len(data)
            max_scale = 1.0 if is_combined else 0.5
            width_pct = min(100, (avg_val / max_scale) * 100)
            html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            html += f'<span style="color:{color};font-weight:700;min-width:120px;font-size:0.85rem;">{team}</span>'
            html += f'<div style="flex:1;background:#1e293b;border-radius:4px;height:20px;overflow:hidden;">'
            html += f'<div style="width:{width_pct:.0f}%;height:100%;background:{color};border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:0.75rem;font-weight:700;color:white;">{avg_val:.2f} abates/min</div></div>'
            html += '</div>'
        html += '</div>'

    html += explain("<b>CKPM</b> indica o ritmo global da partida. CKPM > 0.8 indicam jogos 'sangrentos', cheios de lutas (favorável para Overs de Kills). <b>KPM</b> mede a letalidade bruta de apenas um time.")
    html += '</div>'
    return html


def gen_economy_cards(s1, s2, t1, t2):
    """Métricas de Economia: EGPM e DPM."""
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
            data = float_list(stats.get(key, []))
            if not data:
                continue
            st = calc_stats(data)
            html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            html += f'<span style="color:{color};font-weight:700;min-width:120px;font-size:0.85rem;">{team}</span>'
            html += f'<span style="color:#e2e8f0;font-size:0.9rem;">{st["avg"]:.0f}</span> '
            html += f'<span style="color:#64748b;font-size:0.75rem;">(Max: {st["max"]:.0f} / Min: {st["min"]:.0f})</span>'
            html += '</div>'
        html += f'<div style="color:#94a3b8;font-size:0.75rem;border-left:2px solid #334155;padding-left:8px;margin-top:4px;"><i>{exp}</i></div>'
        html += '</div>'

    html += explain("Segundo o artigo <i>LoL's Advanced Stats Problem</i>, olhar apenas para KDA é uma armadilha. A verdadeira pressão do jogo provém de <b>Ouro Ganho (EGPM)</b> e <b>Dano Gerado (DPM)</b>.")
    html += '</div>'
    return html


# ============================================================================
# Oracle's Elixir Meta-Models: EGR & MLR
# ============================================================================

def gen_first_objectives_egr(s1, s2, t1, t2):
    """Early Game Rating Proxy (First Blood, Dragon, Herald)."""
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#e2e8f0;margin:0 0 16px 0;font-size:1rem;">⚡ Early-Game Rating (EGR) Proxy — Primeiros Objetivos</h3>'

    fb1, fb2 = s1["fb_rate"], s2["fb_rate"]
    fd1, fd2 = s1["fd_rate"], s2["fd_rate"]
    fh1, fh2 = s1["fherald_rate"], s2["fherald_rate"]

    categories = [("First Blood (FB%)", fb1, fb2), ("First Dragon (FD%)", fd1, fd2), ("First Herald (HLD%)", fh1, fh2)]

    for title, v1, v2 in categories:
        html += f'<div style="margin-bottom:12px;">'
        html += f'<div style="color:#cbd5e1;font-weight:600;font-size:0.85rem;margin-bottom:4px;">{title}</div>'
        html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
        html += f'<span style="color:#60a5fa;font-weight:700;min-width:40px;text-align:right;font-size:0.8rem;">{v1:.0f}%</span>'
        html += f'<div style="flex:1;background:#1e293b;border-radius:4px;height:12px;overflow:hidden;">'
        html += f'<div style="width:{v1:.0f}%;height:100%;background:#3b82f6;border-radius:4px;"></div></div></div>'
        html += f'<div style="display:flex;align-items:center;gap:8px;">'
        html += f'<span style="color:#f87171;font-weight:700;min-width:40px;text-align:right;font-size:0.8rem;">{v2:.0f}%</span>'
        html += f'<div style="flex:1;background:#1e293b;border-radius:4px;height:12px;overflow:hidden;">'
        html += f'<div style="width:{v2:.0f}%;height:100%;background:#ef4444;border-radius:4px;"></div></div></div>'
        html += '</div>'

    html += explain("O modelo de <b>EGR</b> do Oracle's Elixir demonstra que o time que conquista esses prêmios iniciais cria uma vantagem de ouro aos 15 minutos que se converte numa <b>Probabilidade de Vitória (Odds)</b> gigantesca. Observe a discrepância nas barras.")
    html += '</div>'
    return html


def gen_mlr_proxy(s1, s2, t1, t2):
    """Mid/Late Rating Proxy (Barons, Inhibitors, Towers)."""
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
    html += explain("O modelo <b>MLR</b> mostra como o time fecha o jogo no Mid-Late Game. Ter Barões sem destruir Inibidores e Torres indica um time passivo que não consegue <i>snowballar</i> sua vantagem. Excelente para apostas no <b>Handicap de Torres</b>.")
    html += '</div>'
    return html


# ============================================================================
# Plotly Distribution Charts
# ============================================================================

def gen_total_abates(s1, s2, t1, t2):
    """Distribuição do total de kills combinadas na partida."""
    k1 = int_list(s1.get("kills_history", []))
    k2 = int_list(s2.get("kills_history", []))
    min_len = min(len(k1), len(k2))
    if min_len == 0:
        return ""
    total = [k1[i] + k2[i] for i in range(min_len)]
    st = calc_stats(total)
    counts = Counter(total)
    x_vals = sorted(counts.keys())
    y_vals = [counts[v] for v in x_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_vals, y=y_vals, marker_color="#a78bfa", marker_line_color="#c4b5fd", marker_line_width=1, text=[str(c) for c in y_vals], textposition="outside"))
    fig.add_vline(x=st["avg"], line=dict(color="#a78bfa", width=2.5, dash="dash"))
    layout = base_layout(f"⚔️ Total de Abates na Partida — {t1} vs {t2}", height=380)
    layout["xaxis"]["title"] = "Total de Kills no Jogo"
    layout["yaxis"]["title"] = "Nº de Jogos"
    fig.update_layout(**layout)

    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas sugeridas (Total Kills):</b><br>'
    for lv in [st["avg"] - 5, st["avg"] - 2.5, st["avg"], st["avg"] + 2.5, st["avg"] + 5]:
        line_v = round(lv * 2) / 2
        prob_over = sum(1 for v in total if v > line_v) / len(total) * 100
        prob_under = 100 - prob_over
        bets += bet_line(f"{t1}+{t2}", "Over", f"{line_v:.1f} kills", prob_over, len(total),
            f"Em {sum(1 for v in total if v > line_v)} de {len(total)} jogos o total de kills foi > {line_v:.1f}. "
            f"Média histórica: {st['avg']:.1f}, Mediana: {st['med']:.1f}, Desvio Padrão: {st['std']:.1f}. "
            f"{'Alta confiança: a linha está abaixo da média.' if line_v < st['avg'] else 'Linha acima da média: depende de jogos sangrentos (alto CKPM).'}")
        bets += bet_line(f"{t1}+{t2}", "Under", f"{line_v:.1f} kills", prob_under, len(total),
            f"Em {sum(1 for v in total if v <= line_v)} de {len(total)} jogos o total de kills foi ≤ {line_v:.1f}. "
            f"{'Conservador: linha acima da média favorece Under.' if line_v > st['avg'] else 'Arriscado: linha abaixo da média desfavorece Under.'}")
        bets += '<br>'
    bets += '</div>'

    return (fig_to_html(fig) + f'<div style="margin-top:8px;">{stats_html(st)}</div>' + bets
            + explain("A distribuição do <b>total de kills na partida</b> (soma). É guiada pela métrica global <b>CKPM</b> detalhada acima. Em jogos com times sanguinários, a cauda longa no gráfico encosta nos 40-50 abates."))


def gen_kills_por_time(s1, s2, t1, t2):
    """Distribuição de kills por time (subplots lado a lado)."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    stats_htmls = []
    for col, (stats, team, bar_color, line_color) in enumerate([(s1, t1, "#3b82f6", "#60a5fa"), (s2, t2, "#ef4444", "#f87171")], 1):
        raw = int_list(stats.get("kills_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_color, marker_line_color=line_color, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_color, width=2.5, dash="dash"), row=1, col=col)
        avg_line = round(st["avg"] * 2) / 2
        pct_over = sum(1 for v in raw if v > avg_line) / len(raw) * 100
        stats_htmls.append(f'<div style="margin-top:4px;"><span style="color:{line_color};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(pct_over)} <b>Over {avg_line:.1f} kills</b></div>')

    layout = base_layout("🎯 Distribuição de Kills Individuais", height=420)
    layout["xaxis"] = dict(title="Kills do Time", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Kills do Time", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)
    return (fig_to_html(fig) + "".join(stats_htmls)
            + explain("A <b>Odd ideal</b> exibida refere-se à entrada <b>Over X.X kills</b> (arredondamento da média). Se o time puxar mais que a média histórica, a linha é coberta. Kills por time medem a pressão terminal, mas times com alta kill rate sem EGR alto podem estar apenas sendo engajados frequentemente."))


def gen_handicap(s1, s2, t1, t2):
    """Gráfico de Handicap (kill diff) com entradas de aposta e explicação."""
    fig = go.Figure()
    odds_html = ""
    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas de Handicap sugeridas:</b><br>'
    for st_data, team, bar_col, line_col in [(s1, t1, "rgba(59,130,246,0.7)", "#60a5fa"), (s2, t2, "rgba(239,68,68,0.7)", "#f87171")]:
        data = [int(round(v)) for v in st_data.get("kill_diff_history", []) if v is not None]
        if not data:
            continue
        st = calc_stats(data)
        counts = Counter(data)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=f"{team} (μ={st['avg']:+.1f})", marker_color=bar_col, marker_line_color=line_col, marker_line_width=1))
        pct_pos = sum(1 for v in data if v > 0) / len(data) * 100
        odds_html += f'<div style="margin-top:4px;"><span style="color:{line_col};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(pct_pos)} <b>Handicap 0 (Positivo > 0 kills)</b></div>'

        for hc_line in [-7.5, -5.5, -3.5, -1.5, 0, 1.5, 3.5, 5.5, 7.5]:
            prob = sum(1 for v in data if v > hc_line) / len(data) * 100
            sign = "+" if hc_line >= 0 else ""
            bets += bet_line(team, "Handicap", f"{sign}{hc_line:.1f} kills", prob, len(data),
                f"Em {sum(1 for v in data if v > hc_line)} de {len(data)} jogos, {team} teve diff > {hc_line:+.1f}. "
                f"Média de handicap: {st['avg']:+.1f}, Mediana: {st['med']:+.1f}, Desvio Padrão: {st['std']:.1f}. "
                f"{'Linha conservadora abaixo da média — alta cobertura.' if hc_line < st['avg'] else 'Linha agressiva acima da média — precisa de domínio claro.'}")
        bets += '<br>'
    bets += '</div>'

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
    layout = base_layout("📊 Handicap de Kills (Kill Diff)", height=380)
    layout["barmode"] = "overlay"
    layout["xaxis"]["title"] = "Diferença de Kills (positivo = dominou)"
    fig.update_layout(**layout)
    return (fig_to_html(fig) + odds_html + handicap_explain + bets
            + explain("A <b>Odd ideal</b> mostrada acima refere-se à entrada <b>Handicap 0</b> (mais kills que mortes). Clique nas entradas para ver o detalhamento individual."))


def gen_duracao(s1, s2, t1, t2):
    """Distribuição de duração do mapa com entradas Over/Under."""
    all_dur = [v for v in s1.get("duration_history", []) + s2.get("duration_history", []) if v]
    if not all_dur:
        return ""
    st = calc_stats(all_dur)
    fig = go.Figure()
    for stats, team, color in [(s1, t1, "rgba(59,130,246,0.55)"), (s2, t2, "rgba(239,68,68,0.55)")]:
        data = [v for v in stats.get("duration_history", []) if v]
        if data:
            fig.add_trace(go.Histogram(x=data, name=team, marker_color=color, opacity=0.7, xbins=dict(size=2)))
    fig.add_vline(x=st["avg"], line=dict(color="#22c55e", width=2.5, dash="dash"))
    layout = base_layout("⏱️ Duração do Mapa (Pace Control)", height=380)
    layout["barmode"] = "overlay"
    layout["xaxis"]["title"] = "Duração (minutos)"
    fig.update_layout(**layout)

    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas de Duração sugeridas:</b><br>'
    for lv in [25.5, 28.5, 31.5, 34.5, 37.5]:
        p_over = sum(1 for v in all_dur if v > lv) / len(all_dur) * 100
        p_under = 100 - p_over
        bets += bet_line(f"{t1}+{t2}", "Over", f"{lv}min", p_over, len(all_dur),
            f"Em {sum(1 for v in all_dur if v > lv)} de {len(all_dur)} jogos a duração excedeu {lv}min. "
            f"Média: {st['avg']:.1f}min, Mediana: {st['med']:.1f}min. "
            f"{'Linha conservadora.' if lv < st['avg'] else 'Linha agressiva — requer jogos longos.'}")
        bets += bet_line(f"{t1}+{t2}", "Under", f"{lv}min", p_under, len(all_dur),
            f"Em {sum(1 for v in all_dur if v <= lv)} de {len(all_dur)} jogos a duração foi ≤ {lv}min. "
            f"{'Favorável: linha acima da média.' if lv > st['avg'] else 'Arriscado: linha abaixo da média.'}")
        bets += '<br>'
    bets += '</div>'

    return (fig_to_html(fig) + f'<div style="margin-top:8px;">{stats_html(st, "min")}</div>' + bets
            + explain("A <b>Duração (AGT - Avg Game Time)</b> reflete se os times controlam o pace. Um time de EGR baixo e AGT alto joga na defensiva pelas torres e falha nas chamadas de Barão."))


# ============================================================================
# Objective Distribution Charts (Dragons, Torres, Barões)
# ============================================================================

def gen_dragons(s1, s2, t1, t2):
    """Distribuição de dragões por time (subplots lado a lado) + totais combinados."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    combo_html = ""
    for col, (stats, team, bar_c, line_c) in enumerate([(s1, t1, "#f97316", "#fb923c"), (s2, t2, "#c2410c", "#ea580c")], 1):
        raw = int_list(stats.get("dragons_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_c, marker_line_color=line_c, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_c, width=2.5, dash="dash"), row=1, col=col)
        combo_html += f'<div style="margin-top:4px;"><span style="color:{line_c};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(sum(1 for v in raw if v > 3.5)/len(raw)*100)} <b>Over 3.5 Dragões</b></div>'

    layout = base_layout("🐉 Distribuição de Dragões por Time", height=400)
    layout["xaxis"] = dict(title="Dragões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Dragões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)

    # Total combinado
    d1 = int_list(s1.get("dragons_history", []))
    d2 = int_list(s2.get("dragons_history", []))
    min_len = min(len(d1), len(d2))
    total_html = ""
    if min_len > 0:
        total = [d1[i] + d2[i] for i in range(min_len)]
        st_t = calc_stats(total)
        bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas Total Dragões (Partida):</b><br>'
        for lv in [3.5, 4.5, 5.5]:
            prob_o = sum(1 for v in total if v > lv) / len(total) * 100
            bets += bet_line(f"{t1}+{t2}", "Over", f"{lv:.1f} dragões", prob_o, len(total),
                f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de dragões foi > {lv:.1f}. "
                f"Média combinada: {st_t['avg']:.1f}. Dragon Soul exige 4 dragões para um time.")
            bets += '<br>'
        bets += '</div>'
        total_html = f'<div style="margin-top:8px;">{stats_html(st_t, " dragões (total)")}</div>' + bets

    return (fig_to_html(fig) + combo_html + total_html
            + explain("O controle de <b>Dragões</b> é um proxy do domínio bot-side e da visão do rio. Times com FD% alto tendem a acumular 3-4 dragões de modo mais consisteente. O Dragon Soul (~4 dragões) é um gamechanger."))


def gen_torres(s1, s2, t1, t2):
    """Distribuição de torres destruídas por time (subplots lado a lado)."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    combo_html = ""
    for col, (stats, team, bar_c, line_c) in enumerate([(s1, t1, "#eab308", "#fbbf24"), (s2, t2, "#a16207", "#ca8a04")], 1):
        raw = int_list(stats.get("towers_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_c, marker_line_color=line_c, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_c, width=2.5, dash="dash"), row=1, col=col)
        combo_html += f'<div style="margin-top:4px;"><span style="color:{line_c};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(sum(1 for v in raw if v > 5.5)/len(raw)*100)} <b>Over 5.5 Torres</b></div>'

    layout = base_layout("🏰 Distribuição de Torres Destruídas por Time", height=400)
    layout["xaxis"] = dict(title="Torres Destruídas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Torres Destruídas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)

    # Total combinado
    t1_d = int_list(s1.get("towers_history", []))
    t2_d = int_list(s2.get("towers_history", []))
    min_len = min(len(t1_d), len(t2_d))
    total_html = ""
    if min_len > 0:
        total = [t1_d[i] + t2_d[i] for i in range(min_len)]
        st_t = calc_stats(total)
        bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas Total Torres (Partida):</b><br>'
        for lv in [10.5, 12.5, 14.5]:
            prob_o = sum(1 for v in total if v > lv) / len(total) * 100
            bets += bet_line(f"{t1}+{t2}", "Over", f"{lv:.1f} torres", prob_o, len(total),
                f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de torres foi > {lv:.1f}. "
                f"Média combinada: {st_t['avg']:.1f}. Existem 11 torres por time (22 no total).")
            bets += '<br>'
        bets += '</div>'
        total_html = f'<div style="margin-top:8px;">{stats_html(st_t, " torres (total)")}</div>' + bets

    return (fig_to_html(fig) + combo_html + total_html
            + explain("O <b>MLR (Mid/Late Rating)</b> mostra que torres destruídas indicam conversão de vantagem. Times que pegam Barão mas não derrubam torres são passivos e falham em <i>snowballar</i>."))


def gen_baroes(s1, s2, t1, t2):
    """Distribuição de barões por time (subplots lado a lado)."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    combo_html = ""
    for col, (stats, team, bar_c, line_c) in enumerate([(s1, t1, "#22c55e", "#4ade80"), (s2, t2, "#15803d", "#16a34a")], 1):
        raw = int_list(stats.get("barons_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_c, marker_line_color=line_c, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_c, width=2.5, dash="dash"), row=1, col=col)
        combo_html += f'<div style="margin-top:4px;"><span style="color:{line_c};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(sum(1 for v in raw if v > 0.5)/len(raw)*100)} <b>Over 0.5 Barões</b></div>'

    layout = base_layout("💚 Distribuição de Barões por Time", height=400)
    layout["xaxis"] = dict(title="Barões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Barões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)

    # Total combinado
    b1 = int_list(s1.get("barons_history", []))
    b2 = int_list(s2.get("barons_history", []))
    min_len = min(len(b1), len(b2))
    total_html = ""
    if min_len > 0:
        total = [b1[i] + b2[i] for i in range(min_len)]
        st_t = calc_stats(total)
        bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas Total Barões (Partida):</b><br>'
        for lv in [0.5, 1.5]:
            prob_o = sum(1 for v in total if v > lv) / len(total) * 100
            bets += bet_line(f"{t1}+{t2}", "Over", f"{lv:.1f} barões", prob_o, len(total),
                f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de barões foi > {lv:.1f}. "
                f"Média combinada: {st_t['avg']:.1f}. Jogos que ultrapassam 25min tendem a ter pelo menos 1 Barão.")
            bets += '<br>'
        bets += '</div>'
        total_html = f'<div style="margin-top:8px;">{stats_html(st_t, " barões (total)")}</div>' + bets

    return (fig_to_html(fig) + combo_html + total_html
            + explain("O <b>Barão Nashor</b> é o principal indicador do MLR. Seu buff de empurro de lanes permite cercar torres e inibidores. Times que controlam o Baron Pit ditam o ritmo do mid-late game."))

