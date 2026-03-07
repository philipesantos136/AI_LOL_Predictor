"""
charts/ev_finder.py — Expected Value Finder (Odd Mining).
Gera recomendações de apostas por time e mercado usando análise cruzada Oracle's Elixir.
"""

import re

from .html_helpers import calc_stats, float_list, bet_line


# ============================================================================
# Helpers Internos
# ============================================================================

def _rate_prob(data, cond):
    """Calcula (probabilidade%, count) de uma condição sobre dados."""
    v = [x for x in data if x is not None]
    return (sum(1 for x in v if cond(x)) / len(v) * 100, len(v)) if v else (None, 0)


def _extract_prob(entry_html):
    """Extrai o valor de probabilidade de uma string HTML de bet_line."""
    m = re.search(r'\((\d+)%\)', entry_html)
    return int(m.group(1)) if m else 0


# ============================================================================
# Market Groups Definition
# ============================================================================

TEAM_MARKETS = [
    ("Vencedor (ML)",  "🏆 Vencedor",         "#6366f1", "Moneyline"),
    ("Handicap",       "📊 Handicap de Kills", "#a78bfa", "Kill Diff"),
    ("Over Kills",     "⚔️ Over Kills Individuais", "#60a5fa", "Kills do Time"),
    ("First Blood",    "🩸 First Blood",        "#ef4444", "EGR component"),
    ("First Dragon",   "🐲 First Dragon",       "#fb923c", "EGR component"),
    ("Corrida Abates", "🏃 Corrida de Abates", "#10b981", "First to X Kills (Proxy)"),
]

JOINT_MARKETS = [
    ("Total Kills",    "💥 Total de Kills (Partida)", "#ec4899", "Soma Estimada"),
    ("Total Dragões",  "🐉 Total de Dragões",         "#f97316", "Soma Estimada"),
    ("Total Torres",   "🏰 Total de Torres",          "#eab308", "Soma Estimada"),
    ("Total Barões",   "💚 Total de Barões",          "#22c55e", "Soma Estimada"),
    ("Over Duração",   "⏱️ Over Duração",            "#06b6d4", "Pool Combinada"),
]

# ============================================================================
# Team Entry Generators
# ============================================================================

def _gen_winner_entries(stats, team, n, fb, fd, fh):
    """Gera entradas para Vencedor (Moneyline)."""
    wr = stats["win_rate"]
    egr_score = (fb + fd + fh) / 3
    mlr_indicators = (stats["avg_barons"] + stats["avg_inhibitors"] + stats["avg_towers"] / 5) / 3
    combined_score = wr * 0.5 + egr_score * 0.3 + min(mlr_indicators * 20, 100) * 0.2
    return [bet_line(team, "Vencedor (ML)", "Moneyline", wr, n,
        f"Win Rate histórico: {wr:.1f}%. "
        f"EGR Proxy Score (FB%+FD%+HLD%)/3: {egr_score:.0f}%. "
        f"MLR Proxy (Barões+Inibs+Torres): {mlr_indicators:.2f}. "
        f"Score Combinado (50% WR + 30% EGR + 20% MLR): {combined_score:.0f}%. "
        f"Segundo o artigo 'What Are the Odds?', a probabilidade real de vitória "
        f"é melhor estimada combinando múltiplas métricas do que usando Win Rate isolado. "
        f"Se o time domina o Early (EGR alto) E fecha jogos (MLR alto), o WR tende a subestimar a força real.")]


def _gen_over_kills_entries(stats, team, kills, avg_k, egpm_data, dpm_data):
    """Gera entradas Over Kills por time."""
    entries = []
    for line in [round((avg_k - 2) * 2) / 2, round(avg_k * 2) / 2, round((avg_k + 2) * 2) / 2]:
        prob_o, cnt = _rate_prob(kills, lambda v, l=line: v > l)
        if prob_o is not None and prob_o > 5:
            egpm_avg = sum(float_list(egpm_data)) / len(float_list(egpm_data)) if float_list(egpm_data) else 0
            dpm_avg = sum(float_list(dpm_data)) / len(float_list(dpm_data)) if float_list(dpm_data) else 0
            entries.append(bet_line(team, "Over Kills", f"{line:.1f}", prob_o, cnt,
                f"Em {sum(1 for v in kills if v is not None and v > line)} de {cnt} jogos, {team} fez > {line:.1f} kills. "
                f"Média: {avg_k:.1f}, KPM médio: {stats['avg_kpm']:.2f}, CKPM: {stats['avg_ckpm']:.2f}. "
                f"EGPM ({egpm_avg:.0f}/min) e DPM ({dpm_avg:.0f}/min) "
                f"indicam {'pressão ofensiva alta' if stats['avg_kpm'] > 0.3 else 'estilo mais passivo'}. "
                f"{'Alta CKPM sugere jogos sangrentos — favorável para Overs.' if stats['avg_ckpm'] > 0.7 else 'CKPM moderada/baixa — Overs agressivos são arriscados.'}"))
    return entries


def _gen_handicap_entries(stats, team, kd):
    """Gera entradas Handicap de Kills."""
    if not kd:
        return []
    entries = []
    st_kd = calc_stats(kd)
    for hc in [-5.5, -3.5, -1.5, 0, 1.5, 3.5, 5.5]:
        prob_hc, cnt = _rate_prob(kd, lambda v, h=hc: v > h)
        if prob_hc is not None and prob_hc > 5:
            sign = "+" if hc >= 0 else ""
            entries.append(bet_line(team, "Handicap", f"{sign}{hc:.1f} kills", prob_hc, cnt,
                f"Em {sum(1 for v in kd if v is not None and v > hc)} de {cnt} jogos, {team} teve diff > {hc:+.1f}. "
                f"Média de handicap: {st_kd['avg']:+.1f}, σ: {st_kd['std']:.1f}. "
                f"O artigo 'Significant Statistics' mostra que a diferença de kills está diretamente "
                f"ligada ao Gold Difference — cada kill vale ~300-450 Gold dependendo do shutdown. "
                f"{'Linha conservadora (negativa) — protege contra jogos ruins.' if hc < 0 else 'Linha agressiva — precisa de domínio claro no Early+Mid Game.'}"))
    return entries

def _gen_first_to_x_kills(stats, team, opp_stats, n):
    """Proxy Model para First to 5, 10, 15 kills baseado no KPM e EGR."""
    entries = []
    kpm_diff = stats['avg_kpm'] - opp_stats['avg_kpm']
    fb = stats['fb_rate']
    wr = stats["win_rate"]
    
    # Base formula (proxy): advantage shifts progressively with game length
    prob_5 = min(max((fb * 0.6) + (kpm_diff * 40) + 20, 10), 90)
    prob_10 = min(max((fb * 0.4) + (kpm_diff * 60) + 30, 10), 90)
    prob_15 = min(max((wr * 0.5) + (kpm_diff * 80) + 25, 10), 90)

    math_base = (
        "<br><br><b>🧮 Matemática do Proxy Model:</b><br>"
        "Como a métrica exata não está no banco, usamos uma regressão baseada em:<br>"
        f"• <b>FB% ({fb:.0f}%):</b> Taxa de First Blood (peso maior no 'First to 5').<br>"
        f"• <b>KPM Diff ({kpm_diff:+.2f}):</b> Diferença de agressividade entre os times.<br>"
        f"• <b>WR ({wr:.0f}%):</b> Probabilidade de vitória histórica (peso no 'First to 15').<br><br>"
    )

    entries.append(bet_line(team, "Corrida Abates", "Primeiro a 5 Kills", prob_5, n,
        f"Estimativa Proxy para os primeiros abates do jogo. {math_base}"
        "<b>Fórmula:</b> (FB% × 0.6) + (KPM_Diff × 40) + 20. "
        "Foca no domínio mecânico inicial e priority de lane."))
    
    entries.append(bet_line(team, "Corrida Abates", "Primeiro a 10 Kills", prob_10, n,
        f"Estimativa Proxy para a transição para o Mid Game. {math_base}"
        "<b>Fórmula:</b> (FB% × 0.4) + (KPM_Diff × 60) + 30. "
        "Equilibra o First Blood com a taxa de kills sustentada (KPM)."))
        
    entries.append(bet_line(team, "Corrida Abates", "Primeiro a 15 Kills", prob_15, n,
        f"Estimativa Proxy para o domínio do mapa no Mid-Late Game. {math_base}"
        "<b>Fórmula:</b> (WR% × 0.5) + (KPM_Diff × 80) + 25. "
        "Foca na capacidade de fechar lutas e converter vantagens."))
    
    return entries

# ============================================================================
# Joint Match Generators (Soma ou Combinação)
# ============================================================================

def _gen_joint_totals(arr1, arr2, market, lines_func, explain_text):
    if not arr1 or not arr2: return []
    min_len = min(len(arr1), len(arr2))
    joint_data = [arr1[i] + arr2[i] for i in range(min_len)]
    st = calc_stats(joint_data)
    avg = st['avg']
    
    entries = []
    lines = lines_func(avg)
    for line in lines:
        prob, cnt = _rate_prob(joint_data, lambda v, l=line: v > l)
        if prob is not None and prob > 5:
            entries.append(bet_line("Partida", market, f"Over {line}", prob, cnt,
                f"Soma do histórico dos dois times ({cnt} pares combinados aleatoriamente). "
                f"Média Combinada Estimada: {avg:.1f}. {explain_text}"))
    return entries

# ============================================================================
# Main Generator
# ============================================================================

def gen_betting_recommendations(s1, s2, t1, t2):
    """Expected Value Finder completo — gera entradas organizadas por time → mercado → risco."""
    html = ""
    categories = []

    # 1. Team-Specific Markets
    for stats, opp_stats, team, tcolor in [(s1, s2, t1, "#60a5fa"), (s2, s1, t2, "#f87171")]:
        kills = stats.get("kills_history", [])
        kd = stats.get("kill_diff_history", [])
        n = stats["total_games"]
        
        entries = []
        entries.extend(_gen_winner_entries(stats, team, n, stats["fb_rate"], stats["fd_rate"], stats["fherald_rate"]))
        entries.extend(_gen_over_kills_entries(stats, team, kills, stats["avg_kills"], stats.get("earnedgold_pm_history", []), stats.get("dmg_pm_history", [])))
        entries.extend(_gen_handicap_entries(stats, team, kd))
        entries.extend(_gen_first_to_x_kills(stats, team, opp_stats, n))

        entries.append(bet_line(team, "First Blood", "Sim", stats["fb_rate"], n, 
            f"FB% histórico de {team}: {stats['fb_rate']:.0f}% em {n} jogos. O EGR (Early-Game Rating) é parcialmente determinado pelo First Blood."))
        entries.append(bet_line(team, "First Dragon", "Sim", stats["fd_rate"], n, 
            f"FD% de {team}: {stats['fd_rate']:.0f}% em {n} jogos. FD% > 55% combinada com FB% > 50% cria um EGR dominante."))

        entries = [e for e in entries if e]
        if entries:
            categories.append((team, tcolor, entries, TEAM_MARKETS))

    # 2. Joint / Match Markets (Soma dos dois)
    joint_entries = []
    
    k1 = [v for v in s1.get("kills_history", []) if v is not None]
    k2 = [v for v in s2.get("kills_history", []) if v is not None]
    if k1 and k2:
        joint_entries.extend(_gen_joint_totals(k1, k2, "Total Kills", lambda a: [round((a-5)*2)/2, round(a*2)/2, round((a+5)*2)/2], "Forte dependência do CKPM combinado (partidas sangrentas)."))
    
    d1 = [v for v in s1.get("dragons_history", []) if v is not None]
    d2 = [v for v in s2.get("dragons_history", []) if v is not None]
    if d1 and d2:
        joint_entries.extend(_gen_joint_totals(d1, d2, "Total Dragões", lambda a: [3.5, 4.5, 5.5], "Reflete times que trocam objetivos (Soul games longos aumentam o limite para > 4.5)."))
    
    t1_h = [v for v in s1.get("towers_history", []) if v is not None]
    t2_h = [v for v in s2.get("towers_history", []) if v is not None]
    if t1_h and t2_h:
        joint_entries.extend(_gen_joint_totals(t1_h, t2_h, "Total Torres", lambda a: [10.5, 12.5, 14.5], "Jogos mais longos e disputados geram quebras nas duas bases. Média de torres destruídas combinada reflete o ritmo de mid-game."))
    
    b1 = [v for v in s1.get("barons_history", []) if v is not None]
    b2 = [v for v in s2.get("barons_history", []) if v is not None]
    if b1 and b2:
        joint_entries.extend(_gen_joint_totals(b1, b2, "Total Barões", lambda a: [0.5, 1.5], "Partidas caóticas e longas = múltiplos Nashors roubados/trocados."))
    
    # Duration combines probabilities (Union of histories)
    all_dur = [v for v in s1.get("duration_history", []) + s2.get("duration_history", []) if v]
    if all_dur:
        st_dur = calc_stats(all_dur)
        for dl in [28.5, 31.5, 34.5]:
            prob_do, cnt = _rate_prob(all_dur, lambda v, l=dl: v > l)
            if prob_do is not None and prob_do > 5:
                joint_entries.append(bet_line(f"Partida", "Over Duração", f"{dl}min", prob_do, cnt,
                    f"Dur. Média (Pool dos 2 times): {st_dur['avg']:.1f}min. "
                    f"Apostas conjuntas calculadas baseadas na união das durações de todas as partidas."))

    if joint_entries:
        categories.append((f"⚔️ {t1} vs {t2} (Estimativas de Jogo)", "#f59e0b", joint_entries, JOINT_MARKETS))

    if not categories:
        return '<div style="background:#1e293b;border-radius:12px;padding:20px;border:1px solid #334155;color:#94a3b8;text-align:center;">📭 Nenhum dado disponível para gerar recomendações.</div>'

    # Renderizar blocos
    for title, tcolor, entries, schema in categories:
        html += (
            f'<div style="background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:14px;'
            f'border:2px solid {tcolor}33;margin-bottom:20px;overflow:hidden;">'
            f'<div style="background:linear-gradient(90deg,{tcolor}22,transparent);'
            f'padding:14px 20px;border-bottom:1px solid {tcolor}33;display:flex;align-items:center;gap:12px;">'
            f'<span style="color:{tcolor};font-weight:800;font-size:1.15rem;">{title}</span>'
            f'<span style="color:#64748b;font-size:0.8rem;">— Entradas de Valor Organizadas</span>'
            f'</div>'
            f'<div style="padding:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;">'
        )

        for market_key, market_label, market_color, market_note in schema:
            group = [e for e in entries if market_key in e]
            if not group:
                continue

            low = sorted([e for e in group if '🟢' in e], key=_extract_prob, reverse=True)
            med = sorted([e for e in group if '🟡' in e], key=_extract_prob, reverse=True)
            high = sorted([e for e in group if '🔴' in e], key=_extract_prob, reverse=True)

            html += (
                f'<div style="background:#1e293b;border-radius:10px;padding:14px;'
                f'border:1px solid #334155;border-top:3px solid {market_color};">'
                f'<div style="color:{market_color};font-weight:700;font-size:0.92rem;margin-bottom:2px;">{market_label}</div>'
                f'<div style="color:#64748b;font-size:0.72rem;margin-bottom:10px;">{market_note}</div>'
            )

            if low:
                html += '<div style="margin-bottom:6px;"><span style="color:#4ade80;font-size:0.72rem;font-weight:700;">🟢 Baixo Risco (≥65%)</span>' + ''.join(low) + '</div>'
            if med:
                html += '<div style="margin-bottom:6px;"><span style="color:#fbbf24;font-size:0.72rem;font-weight:700;">🟡 Risco Médio (50–64%)</span>' + ''.join(med) + '</div>'
            if high:
                html += '<div style="margin-bottom:6px;"><span style="color:#f87171;font-size:0.72rem;font-weight:700;">🔴 Alto Risco (&lt;50%) — Odds Altas</span>' + ''.join(high) + '</div>'

            html += '</div>'

        html += '</div></div>'

    return html
