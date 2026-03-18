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

def _gen_winner_entries(stats, team, n, fb, fd, fh, m_team):
    """Gera entradas para Vencedor (Moneyline)."""
    # Simple proxy effect of early game modifiers on Winrate
    m_fb = m_team.get("firstblood", 1.0) if m_team else 1.0
    m_fd = m_team.get("firstdragon", 1.0) if m_team else 1.0
    m_fh = m_team.get("firstherald", 1.0) if m_team else 1.0
    avg_early_m = (m_fb + m_fd + m_fh) / 3 if m_fb and m_fd and m_fh else 1.0

    wr = stats["win_rate"]
    adj_wr = min(wr * avg_early_m, 95)
    
    egr_score = (fb + fd + fh) / 3
    mlr_indicators = (stats["avg_barons"] + stats["avg_inhibitors"] + stats["avg_towers"] / 5) / 3
    combined_score = adj_wr * 0.5 + egr_score * 0.3 + min(mlr_indicators * 20, 100) * 0.2
    
    adj_text = ""
    if avg_early_m != 1.0:
        adj_text = f" <span style='color:#c4b5fd;font-size:0.75rem;' title='Multiplicador Baseado no Draft Early Game: {avg_early_m:.2f}x'>✨ Draft ({combined_score:.0f}% proj)</span>"

    return [bet_line(team, "Vencedor (ML)", f"Moneyline{adj_text}", combined_score, n,
        f"Win Rate histórico: {wr:.1f}%. Projeção c/ Draft: {adj_wr:.1f}%. "
        f"EGR Proxy Score (FB%+FD%+HLD%)/3: {egr_score:.0f}%. "
        f"MLR Proxy (Barões+Inibs+Torres): {mlr_indicators:.2f}. "
        f"Score Combinado: {combined_score:.0f}%.",
        f"<b>💡 Conselho do Draft:</b> Sinergias escolhidas alteram a Força de Early Game em <b>{avg_early_m:.2f}x</b>. "
        f"Se o time domina o Early E fecha jogos, as chances reais de vitória divergem do WR bruto.")]


def _gen_over_kills_entries(stats, team, kills, avg_k, egpm_data, dpm_data, mult=1.0):
    """Gera entradas Over Kills por time."""
    entries = []
    adj_kills = [(v * mult) for v in kills if v is not None] if kills else []
    avg_adj = sum(adj_kills) / len(adj_kills) if adj_kills else avg_k
    
    for line in [round((avg_k - 2) * 2) / 2, round(avg_k * 2) / 2, round((avg_k + 2) * 2) / 2]:
        prob_o, cnt = _rate_prob(adj_kills, lambda v, l=line: v > l)
        
        adj_text = ""
        if mult != 1.0:
            adj_text = f" <span style='color:#c4b5fd;font-size:0.75rem;' title='Multiplicador de Draft: {mult:.2f}x'>✨ Draft ({avg_adj:.1f} proj)</span>"

        if prob_o is not None and prob_o > 5:
            egpm_avg = sum(float_list(egpm_data)) / len(float_list(egpm_data)) if float_list(egpm_data) else 0
            dpm_avg = sum(float_list(dpm_data)) / len(float_list(dpm_data)) if float_list(dpm_data) else 0
            entries.append(bet_line(team, "Over Kills", f"{line:.1f}{adj_text}", prob_o, cnt,
                f"Em {sum(1 for v in adj_kills if v > line)} simulações ajustadas (de {cnt} reais), a projeção passa de {line:.1f}. "
                f"Multiplicador do draft: <b>{mult:.2f}x</b>. Média Histórica {avg_k:.1f} ➡️ <b>{avg_adj:.1f} proj</b>.<br>"
                f"KPM: {stats['avg_kpm']:.2f}, CKPM: {stats['avg_ckpm']:.2f}. "
                f"EGPM ({egpm_avg:.0f}/min) e DPM ({dpm_avg:.0f}/min).",
                f"Apostas em Over dependem de confrontos agressivos (Combate Constante). Se o Draft favorece <b>Pick-offs</b> ou <b>Teamfights</b> frequentes, o 'Over' se torna mais provável."))
    return entries


def _gen_handicap_entries(stats, team, adj_kd, hist_kd, m_team, m_opp):
    """Gera entradas Handicap de Kills."""
    if not adj_kd:
        return []
    entries = []
    st_kd = calc_stats(hist_kd)
    for hc in [-5.5, -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
        prob_hc, cnt = _rate_prob(adj_kd, lambda v, h=hc: v > h)
        
        adj_text = ""
        if m_team != 1.0 or m_opp != 1.0:
            avg_adj = sum(adj_kd) / len(adj_kd) if adj_kd else st_kd['avg']
            adj_text = f" <span style='color:#c4b5fd;font-size:0.75rem;' title='Draft Ajustado'>✨ Draft ({avg_adj:+.1f} proj)</span>"
            
        if prob_hc is not None and prob_hc > 5:
            sign = "+" if hc >= 0 else ""
            entries.append(bet_line(team, "Handicap", f"{sign}{hc:.1f} kills{adj_text}", prob_hc, cnt,
                f"Calculado usando as kills ajustadas pelo draft (Este time: {m_team:.2f}x, Inimigo: {m_opp:.2f}x). "
                f"Diff Histórica Média: {st_kd['avg']:+.1f} ➡️ <b>Projeção c/ Draft: {sum(adj_kd)/len(adj_kd):+.1f}</b>.",
                f"Handicaps negativos exigem que o time não apenas vença, mas <b>atropele (stomp)</b>. Verifique se o Draft tem alto potencial de snowball."))
    return entries

def _gen_first_to_x_kills(stats, team, opp_stats, n, m_team):
    """Proxy Model para First to 5, 10, 15 kills baseado no KPM e EGR."""
    entries = []
    
    m_fb = m_team.get("firstblood", 1.0) if m_team else 1.0
    m_k = m_team.get("kills", 1.0) if m_team else 1.0
    
    kpm_diff = (stats['avg_kpm'] * m_k) - opp_stats['avg_kpm']
    fb = stats['fb_rate'] * m_fb
    wr = stats["win_rate"]
    
    # Base formula (proxy): advantage shifts progressively with game length
    prob_5 = min(max((fb * 0.6) + (kpm_diff * 40) + 20, 10), 90)
    prob_10 = min(max((fb * 0.4) + (kpm_diff * 60) + 30, 10), 90)
    prob_15 = min(max((wr * 0.5) + (kpm_diff * 80) + 25, 10), 90)

    math_base = (
        "<br><br><b>🧮 Matemática do Proxy Model:</b><br>"
        "Usamos uma regressão baseada em:<br>"
        f"• <b>FB% Ajustado ({fb:.0f}%):</b> Taxa (peso maior no 'First to 5', Mult Draft: {m_fb:.2f}x).<br>"
        f"• <b>KPM Diff ({kpm_diff:+.2f}):</b> Diferença de agressividade entre times, após Draft.<br>"
        f"• <b>WR ({wr:.0f}%):</b> Probabilidade de vitória (peso no 'First to 15').<br><br>"
    )

    adj_text = f" <span style='color:#c4b5fd;font-size:0.75rem;' title='Multiplicador do Draft KPM/FB: {m_k:.2f}x'>✨ Draft</span>" if (m_k != 1.0 or m_fb != 1.0) else ""

    entries.append(bet_line(team, "Corrida Abates", f"Primeiro a 5 Kills{adj_text}", prob_5, n,
        f"Estimativa Proxy para os primeiros abates do jogo. {math_base}",
        "<b>Dica:</b> Times com composições de <b>Early Game forte</b> ou <b>Invades</b> planejados costumam vencer essa corrida."))
    
    entries.append(bet_line(team, "Corrida Abates", f"Primeiro a 10 Kills{adj_text}", prob_10, n,
        f"Estimativa Proxy para a transição para o Mid Game. {math_base}",
        "<b>Dica:</b> Ideal para observar após os primeiros Dragões e Arautos, onde as lutas de transição ocorrem."))
    
    entries.append(bet_line(team, "Corrida Abates", f"Primeiro a 15 Kills{adj_text}", prob_15, n,
        f"Estimativa Proxy (Perto do End Game). {math_base}"))
        
    return entries

# ============================================================================
# Joint Match Generators (Soma ou Combinação)
# ============================================================================

def _gen_joint_totals(arr1, arr2, market, lines_func, explain_text, m1=1.0, m2=1.0):
    if not arr1 or not arr2: return []
    min_len = min(len(arr1), len(arr2))
    joint_base = [arr1[i] + arr2[i] for i in range(min_len)]
    joint_adj = [(arr1[i]*m1) + (arr2[i]*m2) for i in range(min_len)]
    st_base = calc_stats(joint_base)
    avg_base = st_base['avg']
    avg_adj = sum(joint_adj) / len(joint_adj) if joint_adj else avg_base
    
    entries = []
    lines = lines_func(avg_base)
    for line in lines:
        prob_adj, cnt = _rate_prob(joint_adj, lambda v, l=line: v > l)
        
        adj_text = ""
        if (m1 != 1.0 or m2 != 1.0):
            adj_text = f" <span style='color:#c4b5fd;font-size:0.75rem;' title='Ajuste de Draft (T1: {m1:.2f}x, T2: {m2:.2f}x)'>✨ Draft ({avg_adj:.1f} proj)</span>"
            
        if prob_adj is not None and prob_adj > 5:
            entries.append(bet_line("Partida", market, f"Over {line}{adj_text}", prob_adj, cnt,
                f"Soma do histórico ajustado pelo impacto dos campeões (T1: {m1:.2f}x, T2: {m2:.2f}x). "
                f"Média Histórica Pura: {avg_base:.1f} ➡️ <b>Projeção c/ Draft: {avg_adj:.1f}</b>.",
                f"<b>Janela:</b> {explain_text}"))
    return entries

# ============================================================================
# Main Generator
# ============================================================================

def gen_betting_recommendations(s1, s2, t1, t2, mult1=None, mult2=None):
    """Expected Value Finder completo — gera entradas organizadas por time → mercado → risco."""
    html = ""
    categories = []

    k1_hist = [v for v in s1.get("kills_history", []) if v is not None]
    k2_hist = [v for v in s2.get("kills_history", []) if v is not None]
    m1_k = mult1.get("kills", 1.0) if mult1 else 1.0
    m2_k = mult2.get("kills", 1.0) if mult2 else 1.0
    
    min_k = min(len(k1_hist), len(k2_hist))
    adj_kd1 = [ (k1_hist[i]*m1_k) - (k2_hist[i]*m2_k) for i in range(min_k) ]
    adj_kd2 = [ (k2_hist[i]*m2_k) - (k1_hist[i]*m1_k) for i in range(min_k) ]

    # 1. Team-Specific Markets
    for stats, opp_stats, team, tcolor in [(s1, s2, t1, "#60a5fa"), (s2, s1, t2, "#f87171")]:
        kills = stats.get("kills_history", [])
        m_team = mult1 if team == t1 else mult2
        m_opp = mult2 if team == t1 else mult1
        
        hist_kd = stats.get("kill_diff_history", [])
        team_adj_kd = adj_kd1 if team == t1 else adj_kd2
        n = stats["total_games"]
        
        m_t_fb = m_team.get("firstblood", 1.0) if m_team else 1.0
        m_t_fd = m_team.get("firstdragon", 1.0) if m_team else 1.0
        
        entries = []
        entries.extend(_gen_winner_entries(stats, team, n, stats["fb_rate"], stats["fd_rate"], stats["fherald_rate"], m_team))
        entries.extend(_gen_over_kills_entries(stats, team, kills, stats["avg_kills"], stats.get("earnedgold_pm_history", []), stats.get("dmg_pm_history", []), m_team.get("kills", 1.0) if m_team else 1.0))
        entries.extend(_gen_handicap_entries(stats, team, team_adj_kd, hist_kd, m_team.get("kills", 1.0) if m_team else 1.0, m_opp.get("kills", 1.0) if m_opp else 1.0))
        entries.extend(_gen_first_to_x_kills(stats, team, opp_stats, n, m_team))

        adj_fb_text = f" <span style='color:#c4b5fd;font-size:0.75rem;'>✨ Draft ({stats['fb_rate']*m_t_fb:.0f}%)</span>" if m_t_fb != 1.0 else ""
        entries.append(bet_line(team, "First Blood", f"Sim{adj_fb_text}", min(stats["fb_rate"] * m_t_fb, 98), n, 
            f"FB% histórico de {team}: {stats['fb_rate']:.0f}% em {n} jogos. Projeção c/ Draft: <b>{stats['fb_rate']*m_t_fb:.0f}%</b>.",
            f"Um Multiplicador de FB de {m_t_fb:.2f}x sinaliza um early game {'poderoso.' if m_t_fb >= 1 else 'defensivo.'}"))

        adj_fd_text = f" <span style='color:#c4b5fd;font-size:0.75rem;'>✨ Draft ({stats['fd_rate']*m_t_fd:.0f}%)</span>" if m_t_fd != 1.0 else ""
        entries.append(bet_line(team, "First Dragon", f"Sim{adj_fd_text}", min(stats["fd_rate"] * m_t_fd, 98), n, 
            f"FD% de {team}: {stats['fd_rate']:.0f}% em {n} jogos. Projeção c/ Draft: <b>{stats['fd_rate']*m_t_fd:.0f}%</b>.",
            f"Indica se a composição tem prioridade no Bot/Rio ({m_t_fd:.2f}x). Se for baixo, o time pode ceder o primeiro dragão para escalar."))

        entries = [e for e in entries if e]
        if entries:
            categories.append((team, tcolor, entries, TEAM_MARKETS))

    # 2. Joint / Match Markets (Soma dos dois)
    m1_k = mult1.get("kills", 1.0) if mult1 else 1.0; m2_k = mult2.get("kills", 1.0) if mult2 else 1.0
    m1_d = mult1.get("dragons", 1.0) if mult1 else 1.0; m2_d = mult2.get("dragons", 1.0) if mult2 else 1.0
    m1_t = mult1.get("towers", 1.0) if mult1 else 1.0; m2_t = mult2.get("towers", 1.0) if mult2 else 1.0
    m1_b = mult1.get("barons", 1.0) if mult1 else 1.0; m2_b = mult2.get("barons", 1.0) if mult2 else 1.0
    m1_dur = mult1.get("duration", 1.0) if mult1 else 1.0; m2_dur = mult2.get("duration", 1.0) if mult2 else 1.0

    joint_entries = []
    
    if k1_hist and k2_hist:
        joint_entries.extend(_gen_joint_totals(k1_hist, k2_hist, "Total Kills", lambda a: [round((a-5)*2)/2, round(a*2)/2, round((a+5)*2)/2], "Forte dependência do CKPM combinado (partidas sangrentas).", m1_k, m2_k))
    
    d1 = [v for v in s1.get("dragons_history", []) if v is not None]
    d2 = [v for v in s2.get("dragons_history", []) if v is not None]
    if d1 and d2:
        joint_entries.extend(_gen_joint_totals(d1, d2, "Total Dragões", lambda a: [3.5, 4.5, 5.5], "Reflete times que trocam objetivos (Soul games longos aumentam o limite para > 4.5).", m1_d, m2_d))
    
    t1_h = [v for v in s1.get("towers_history", []) if v is not None]
    t2_h = [v for v in s2.get("towers_history", []) if v is not None]
    if t1_h and t2_h:
        joint_entries.extend(_gen_joint_totals(t1_h, t2_h, "Total Torres", lambda a: [10.5, 12.5, 14.5], "Jogos mais longos e disputados geram quebras nas duas bases. Média de torres destruídas combinada reflete o ritmo de mid-game.", m1_t, m2_t))
    
    b1 = [v for v in s1.get("barons_history", []) if v is not None]
    b2 = [v for v in s2.get("barons_history", []) if v is not None]
    if b1 and b2:
        joint_entries.extend(_gen_joint_totals(b1, b2, "Total Barões", lambda a: [0.5, 1.5], "Partidas caóticas e longas = múltiplos Nashors roubados/trocados.", m1_b, m2_b))
    
    # Duration combines probabilities (Union of histories)
    all_dur = [v for v in s1.get("duration_history", []) + s2.get("duration_history", []) if v]
    if all_dur:
        m_avg_dur = (m1_dur + m2_dur) / 2
        adj_all_dur = [v * m_avg_dur for v in all_dur]
        st_dur = calc_stats(all_dur)
        adj_dur_avg = sum(adj_all_dur)/len(adj_all_dur)
        for dl in [28.5, 31.5, 34.5]:
            prob_do, cnt = _rate_prob(adj_all_dur, lambda v, l=dl: v > l)
            adj_text = ""
            if m_avg_dur != 1.0:
                adj_text = f" <span style='color:#c4b5fd;font-size:0.75rem;' title='Ajuste Médio Draft: {m_avg_dur:.2f}x'>✨ Draft ({adj_dur_avg:.1f} proj)</span>"
            if prob_do is not None and prob_do > 5:
                joint_entries.append(bet_line(f"Partida", "Over Duração", f"{dl}min{adj_text}", prob_do, cnt,
                    f"Dur. Média Histórica pura: {st_dur['avg']:.1f}min ➡️ <b>Projeção c/ Draft: {adj_dur_avg:.1f}min</b>.",
                    f"<b>Dica:</b> Drafts de <b>Late Game (Scaling)</b> aumentam a chance de Over. Fique atento a times com alto potencial de <b>Waveclear</b> que podem segurar o jogo."))

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
