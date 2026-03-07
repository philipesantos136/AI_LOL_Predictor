"""
charts/renderer.py — Facade Pattern: orquestra todos os módulos e gera o HTML final.
Esta é a única função pública do pacote: generate_charts().
"""

from .html_helpers import INSIGHTS_CSS
from .data_provider import get_team_stats
from .educational import gen_educational_sections
from .chart_generators import (
    gen_winrate_chart, gen_recent_form,
    gen_bloodiness_pace, gen_economy_cards,
    gen_first_objectives_egr, gen_mlr_proxy,
    gen_total_abates, gen_kills_por_time,
    gen_handicap, gen_duracao,
)
from .ev_finder import gen_betting_recommendations


def generate_charts(team1, team2, patches=None, odds_data=None):
    """
    API pública — gera o HTML completo do Advanced Analytics.
    
    Args:
        team1: Nome do time 1
        team2: Nome do time 2
        patches: Lista de patches para filtrar (opcional)
        odds_data: Dados de odds externas (reservado para uso futuro)
    
    Returns:
        String HTML completa com todos os gráficos, análises e recomendações.
    """
    stats1 = get_team_stats(team1, patches)
    stats2 = get_team_stats(team2, patches)

    if not stats1 or not stats2:
        return f"<div style='text-align:center;padding:40px;color:#f87171;'><h3>⚠️ Dados insuficientes</h3></div>"

    patch_label = ", ".join(patches) if patches and "Todos" not in patches else "Todos os patches"

    # Layout constants
    CARD = 'style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;"'
    SECTION = 'style="margin-bottom:24px;"'
    TITLE = 'style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #3b82f6;"'
    TITLE2 = 'style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #a78bfa;"'
    TITLE3 = 'style="color:#eab308;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #eab308;"'

    html = INSIGHTS_CSS + '<div class="insights-container">'

    # Header
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
    html += gen_educational_sections()

    # Modelos Oracle's Elixir (EGR e MLR)
    html += f'<div {SECTION}><div {TITLE3}>🧠 Meta-Modelos Estruturais (EGR e MLR)</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += gen_first_objectives_egr(stats1, stats2, team1, team2)
    html += gen_mlr_proxy(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Economia, Dano e Sangria
    html += f'<div {SECTION}><div {TITLE3}>💥 Advanced Pacing & Economy Context</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += gen_economy_cards(stats1, stats2, team1, team2)
    html += gen_bloodiness_pace(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Win Rate & Momentum
    html += f'<div {SECTION}><div {TITLE}>🏆 Win Rate & Momentum</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_winrate_chart(stats1, stats2, team1, team2)}</div>'
    html += gen_recent_form(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Distribuições de Abates
    html += f'<div {SECTION}><div {TITLE2}>⚔️ Distribuições de Abates (Combate Extremo)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_total_abates(stats1, stats2, team1, team2)}</div>'
    html += f'<div {CARD}>{gen_kills_por_time(stats1, stats2, team1, team2)}</div>'
    html += f'<div {CARD}>{gen_handicap(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'

    # Duração
    html += f'<div {SECTION}><div {TITLE2}>⏱ Duração do Jogo (AGT)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_duracao(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'

    # Expected Value Finder
    html += f'''
    <div style="text-align:center;padding:20px;margin:30px 0 24px 0;background:linear-gradient(135deg,#052e16 0%,#14532d 50%,#052e16 100%);border-radius:16px;border:1px solid rgba(34,197,94,0.3);">
        <h2 style="margin:0;font-size:1.3rem;color:#4ade80;">🎯 Expected Value Finder (Odd Mining)</h2>
        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:0.85rem;">Algoritmo de varredura buscando Edges Estatísticos baseados nos Modelos do Elixir</p>
    </div>
    '''
    html += f'<div {SECTION}>{gen_betting_recommendations(stats1, stats2, team1, team2)}</div>'

    # Footer
    html += f'<div style="text-align:center;color:#64748b;font-size:0.75rem;margin-top:20px;padding:12px;">Camada Silver Analytics | Desenvolvido com Metodologia do Oracle\'s Elixir</div></div>'
    return html
