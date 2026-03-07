"""
charts/educational.py — Seções educativas do Oracle's Elixir.
Glossário, conceitos de EGR/MLR e modelagem de probabilidades.
"""


def gen_educational_sections():
    """Gera o painel educativo com glossário e conceitos do Oracle's Elixir."""
    return '''
    <div style="background:#1e293b;border-radius:12px;padding:24px;border:1px solid #334155;margin-bottom:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3);">
        <h3 style="color:#6366f1;margin:0 0 16px 0;font-size:1.2rem;display:flex;align-items:center;gap:8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
            Oracle's Elixir: Glossário &amp; Conceitos Essenciais
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
                <h4 style="color:#cbd5e1;margin:0 0 10px 0;font-size:0.95rem;">EGR (Early-Game Rating) &amp; MLR (Mid/Late Rating)</h4>
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
