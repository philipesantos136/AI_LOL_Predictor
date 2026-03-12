import gradio as gr
import sqlite3
import os
import sys
import importlib

# Importa módulos de scraping e gráficos
try:
    from interface.scraper_betboom import scrape_match_odds
    from interface.charts import generate_charts
except ImportError as e:
    # Se o erro for que o módulo 'interface' não foi encontrado (execução direta),
    # tenta importar diretamente. Caso contrário (como falta de dependência), relança o erro.
    if "interface" in str(e):
        from scraper_betboom import scrape_match_odds
        from charts import generate_charts
    else:
        raise e

# Adiciona o diretório "pipeline" ao PYTHONPATH para podermos importar os módulos
# Subindo um nível para encontrar o diretório "pipeline" a partir de "interface/"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pipeline")))

# Importa as funções principais de cada script do pipeline (usando importlib pois começam com número)
mod1 = importlib.import_module("1- importador_dados_lol")
baixar_arquivo_mais_recente = mod1.baixar_arquivo_mais_recente

mod2 = importlib.import_module("2- CSV_to_SQLite_lolmatch_datamatches")
csv_to_sqlite = mod2.main

mod3 = importlib.import_module("3- criador_tabela_silver_loldatamatches")
criar_tabela_silver = mod3.criar_tabela_silver

mod4 = importlib.import_module("4- import_2025_matches_to_silver")
popular_tabela_silver = mod4.popular_tabela_silver

mod5 = importlib.import_module("5- ExecutaLLM")
dsa_gera_analises = mod5.dsa_gera_analises

mod_scrape_champs = importlib.import_module("scrape_champions")
baixar_imagens_campeoes = mod_scrape_champs.scrape_champion_squares_ddragon

from pathlib import Path

def get_db_path():
    """Retorna o caminho absoluto do banco de dados."""
    db_path = Path(__file__).parent.parent / "data" / "db" / "lol_datamatches.db"
    # Garante que a pasta existe
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path

def get_times_disponiveis():
    """Busca a lista de times únicos na tabela Silver para preencher os Dropdowns."""
    db_file = get_db_path()
    if not db_file.exists():
        print(f"⚠️ Banco não encontrado em: {db_file}")
        return ["Rode o Pipeline Primeiro"]
        
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT teamname FROM match_data_silver WHERE teamname IS NOT NULL ORDER BY teamname")
            times = [row[0] for row in cursor.fetchall()]
            return times if times else ["Nenhum time encontrado"]
    except Exception as e:
        print(f"❌ Erro ao buscar times: {e}")
        return ["Erro ao carregar times"]

def get_patches_disponiveis():
    """Busca a lista de patches únicos na tabela Silver."""
    db_file = get_db_path()
    if not db_file.exists():
        print(f"⚠️ Banco não encontrado em: {db_file}")
        return ["Todos"]
        
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT patch FROM match_data_silver WHERE patch IS NOT NULL ORDER BY patch DESC")
            patches = [str(row[0]).strip() for row in cursor.fetchall()]
            print(f"✅ Patches carregados: {patches}")
            return ["Todos"] + patches
    except Exception as e:
        print(f"❌ Erro ao buscar patches: {e}")
        return ["Todos"]

def get_campeoes_disponiveis():
    """Busca a lista de campeões na pasta data/champs."""
    champs_dir = Path(__file__).parent.parent / "data" / "champs"
    if not champs_dir.exists():
        return ["Nenhum campeão encontrado"]
    
    # Lista arquivos .png, remove ramificações extras ou pontuações e extrai apenas o nome sem extensão
    campeoes = [f.stem for f in champs_dir.glob("*.png")]
    campeoes.sort()
    return [""] + campeoes if campeoes else ["Nenhum campeão encontrado"]

def executar_pipeline_completo():
    """Executa todas as etapas de ingestão e preparação de dados em sequência."""
    log = ""
    try:
        log += "⏳ Iniciando Download do CSV (Google Drive)...\n"
        baixar_arquivo_mais_recente()
        log += "✅ Download Concluído!\n\n"
        
        log += "⏳ Verificando/Baixando Imagens dos Campeões (Data Dragon)...\n"
        try:
            champs_dir = os.path.join(os.path.dirname(__file__), "..", "data", "champs")
            # a função scrape_champion_squares_ddragon já verifica se a imagem existe antes de baixar
            baixar_imagens_campeoes(champs_dir)
            log += "✅ Imagens Verificadas!\n\n"
        except Exception as img_err:
            log += f"⚠️ Erro no Download de Imagens (Ignorado para o fluxo): {img_err}\n\n"
        
        log += "⏳ Criando/Populando Tabela Bronze (SQLite)...\n"
        csv_to_sqlite()
        log += "✅ Bronze OK!\n\n"
        
        log += "⏳ Criando Estrutura da Tabela Silver...\n"
        criar_tabela_silver()
        log += "✅ Silver Estrutura OK!\n\n"
        
        log += "⏳ Inserindo Dados na Tabela Silver...\n"
        popular_tabela_silver()
        log += "✅ Silver Dados OK!\n\n"

        log += "⏳ Criando/Populando Camada Platinum...\n"
        try:
            mod6 = importlib.import_module("6- criador_tabela_platinum")
            mod6.criar_tabela_platinum()
            mod7 = importlib.import_module("7- popular_tabela_platinum")
            mod7.popular_tabela_platinum()
            log += "✅ Platinum OK!\n\n"
        except Exception as plat_err:
            log += f"⚠️ Erro na Camada Platinum (ignorado para o fluxo principal): {plat_err}\n\n"
        
        log += "🎉 PARABÉNS! Pipeline concluído com sucesso. A base de dados está atualizada e pronta para predições."
        return log
    except Exception as e:
        return f"❌ ERRO DURANTE O PIPELINE: {str(e)}\n\nVerifique os arquivos originais e a conexão de rede."



def gerar_insights(time1, time2, patches, 
                   t1_top, t1_jg, t1_mid, t1_adc, t1_sup,
                   t2_top, t2_jg, t2_mid, t2_adc, t2_sup):
    """Gera gráficos dinâmicos usando dados Silver (instantâneo)."""
    if not time1 or not time2 or time1 == "Rode o Pipeline Primeiro" or time2 == "Rode o Pipeline Primeiro":
        return "<div style='color:#f87171;padding:20px;text-align:center;'>⚠️ Selecione dois times válidos primeiro.</div>"
    if time1 == time2:
        return "<div style='color:#f87171;padding:20px;text-align:center;'>⚠️ Selecione times diferentes.</div>"
    
    # Agrupa os campeões para passar para a função (ignora os vazios/desmarcados)
    champs_t1 = {
        "Top": t1_top if t1_top else None,
        "Jungle": t1_jg if t1_jg else None,
        "Mid": t1_mid if t1_mid else None,
        "ADC": t1_adc if t1_adc else None,
        "Sup": t1_sup if t1_sup else None
    }
    
    champs_t2 = {
        "Top": t2_top if t2_top else None,
        "Jungle": t2_jg if t2_jg else None,
        "Mid": t2_mid if t2_mid else None,
        "ADC": t2_adc if t2_adc else None,
        "Sup": t2_sup if t2_sup else None
    }
    
    try:
        charts_html = generate_charts(time1, time2, patches=patches, odds_data=None, champs_t1=champs_t1, champs_t2=champs_t2)
        return charts_html
    except Exception as e:
        return f"<div style='color:#f87171;padding:20px;text-align:center;'>❌ Erro ao gerar insights: {str(e)}</div>"

def atualizar_dropdowns():
    """Atualiza a lista de times e patches nos dropdowns."""
    times = get_times_disponiveis()
    patches = get_patches_disponiveis()
    return gr.update(choices=times), gr.update(choices=times), gr.update(choices=patches)

def create_interface():
    # --- CSS MINIMALISTA E ROBUSTO ---
    css = """
    .sidebar-menu-btn {
        text-align: left !important;
        width: 100% !important;
        padding: 12px 20px !important;
        margin-bottom: 5px !important;
        border-radius: 8px !important;
        border: none !important;
        background: transparent !important;
        cursor: pointer !important;
        transition: background 0.2s !important;
    }
    .sidebar-menu-btn:hover {
        background: rgba(59, 130, 246, 0.1) !important;
    }
    .sidebar-active {
        background: rgba(59, 130, 246, 0.2) !important;
        border-left: 4px solid #3b82f6 !important;
        font-weight: bold !important;
    }
    .container-boxed {
        background: #1e293b !important;
        border-radius: 12px !important;
        padding: 24px !important;
        border: 1px solid #334155 !important;
        margin-top: 20px !important;
    }
    .main-title {
        text-align: center;
        color: #3b82f6;
        margin-bottom: 2rem !important;
    }
    .caixa-resultado {
        margin-top: 20px;
        min-height: 200px;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 20px;
    }
    .champ-img-box {
        width: 100%;
        max-width: 120px;
        height: 120px;
        margin: 10px auto 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background-color: #0f172a;
        overflow: hidden;
        border: 1px solid #334155;
    }
    .champ-img-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    """

    with gr.Blocks(title="LoL e-Sports Predictor AI") as app:
        # Armazena o CSS em um componente invísivel para o main.py ler se necessário, 
        # ou apenas retornamos ele na função create_interface acompanhando o app
        
        # Estado para controlar qual menu está ativo
        current_view = gr.State("predicao")

        with gr.Sidebar(label="LoL Predictor Menu") as sidebar:
            gr.Markdown("## 🎮 NAVEGAÇÃO")
            btn_menu_predicao = gr.Button("📊 Advanced Analytics", elem_classes=["sidebar-menu-btn", "sidebar-active"])
            btn_menu_pipeline = gr.Button("⚙️ Engenharia de Dados", elem_classes="sidebar-menu-btn")
            
            gr.Markdown("---")
            gr.Markdown("Powered by **Gemini 2.0 Flash**\nLocal Stats Database")
            
        # Conteúdo Principal
        with gr.Column():
            
            # --- SEÇÃO 1: VENCEDOR DA PARTIDA ---
            with gr.Group(visible=True) as group_predicao:
                gr.Markdown("# 📊 Advanced Analytics", elem_classes="main-title")
                
                with gr.Column(elem_classes="container-boxed"):
                    times_originais = get_times_disponiveis()
                    patches_originais = get_patches_disponiveis()
                    
                    with gr.Row():
                        dropdown_t1 = gr.Dropdown(choices=times_originais, value=None, label="🟦 Time 1 (Blue Side)", allow_custom_value=False)
                        dropdown_t2 = gr.Dropdown(choices=times_originais, value=None, label="🟥 Time 2 (Red Side)", allow_custom_value=False)
                    
                    dropdown_patches = gr.Dropdown(
                        choices=patches_originais, 
                        value=patches_originais[1:5] if len(patches_originais) > 1 else ["Todos"], 
                        multiselect=True, 
                        label="📅 Versão do Patch",
                        interactive=True
                    )
                    
                    btn_insights = gr.Button("📊 Gerar Insights", variant="primary")

                with gr.Accordion("⚔️ Champions (Opcional)", open=False, elem_classes="container-boxed"):
                    gr.Markdown("Selecione os campeões para cada rota. Você pode selecionar de apenas um time ou ambos. As estatísticas avançadas serão exibidas nos destaques.")
                    campeoes = get_campeoes_disponiveis()
                    
                    gr.Markdown("### 🟦 Time 1 (Blue Side)")
                    with gr.Row():
                        with gr.Column(scale=1):
                            t1_top = gr.Dropdown(choices=campeoes, value="", label="Top")
                            img_t1_top = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t1_jg = gr.Dropdown(choices=campeoes, value="", label="Jungle")
                            img_t1_jg = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t1_mid = gr.Dropdown(choices=campeoes, value="", label="Mid")
                            img_t1_mid = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t1_adc = gr.Dropdown(choices=campeoes, value="", label="ADC")
                            img_t1_adc = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t1_sup = gr.Dropdown(choices=campeoes, value="", label="Sup")
                            img_t1_sup = gr.HTML("<div class='champ-img-box'></div>")
                            
                    gr.Markdown("### 🟥 Time 2 (Red Side)")
                    with gr.Row():
                        with gr.Column(scale=1):
                            t2_top = gr.Dropdown(choices=campeoes, value="", label="Top")
                            img_t2_top = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t2_jg = gr.Dropdown(choices=campeoes, value="", label="Jungle")
                            img_t2_jg = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t2_mid = gr.Dropdown(choices=campeoes, value="", label="Mid")
                            img_t2_mid = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t2_adc = gr.Dropdown(choices=campeoes, value="", label="ADC")
                            img_t2_adc = gr.HTML("<div class='champ-img-box'></div>")
                            
                        with gr.Column(scale=1):
                            t2_sup = gr.Dropdown(choices=campeoes, value="", label="Sup")
                            img_t2_sup = gr.HTML("<div class='champ-img-box'></div>")

                gr.Markdown("### 📊 Análise Estatística Completa")
                insights_html = gr.HTML(value="<div style='color:#94a3b8;text-align:center;padding:30px;'>Selecione dois times e clique em <b>📊 Gerar Insights</b> para análise estatística completa.</div>")

            # --- SEÇÃO 2: PIPELINE ---
            with gr.Group(visible=False) as group_pipeline:
                gr.Markdown("# ⚙️ Engenharia de Dados", elem_classes="main-title")
                
                with gr.Column(elem_classes="container-boxed"):
                    gr.Markdown("Clique no botão abaixo para baixar os dados mais recentes do Google Drive e atualizar sua base local.")
                    btn_pipeline = gr.Button("🚀 Rodar Pipeline Completo", variant="secondary")
                    console_saida = gr.Textbox(label="Painel de Monitoramento", lines=15, max_lines=20)

        # --- LÓGICA DE NAVEGAÇÃO ---
        def navigate_to_predicao():
            return (
                gr.update(visible=True), 
                gr.update(visible=False), 
                gr.update(elem_classes=["sidebar-menu-btn", "sidebar-active"]),
                gr.update(elem_classes="sidebar-menu-btn")
            )
            
        def navigate_to_pipeline():
            return (
                gr.update(visible=False), 
                gr.update(visible=True), 
                gr.update(elem_classes="sidebar-menu-btn"),
                gr.update(elem_classes=["sidebar-menu-btn", "sidebar-active"])
            )

        btn_menu_predicao.click(
            fn=navigate_to_predicao, 
            outputs=[group_predicao, group_pipeline, btn_menu_predicao, btn_menu_pipeline]
        )
        btn_menu_pipeline.click(
            fn=navigate_to_pipeline, 
            outputs=[group_predicao, group_pipeline, btn_menu_predicao, btn_menu_pipeline]
        )

        def update_champ_img(champ_name):
            if not champ_name:
                return "<div class='champ-img-box'></div>"
            # Get the path to 'data/champs/{champ_name}.png' relative to the browser (using file serving or base64)
            # In Gradio we can return an absolute or relative filepath for components like gr.Image.
            # However for gr.HTML, we must use base64 or serve the file. It's safer to use base64 or simple img tag if served.
            # Alternatively, since we use HTML, we can just load the image locally using base64.
            import base64
            img_path = Path(__file__).parent.parent / "data" / "champs" / f"{champ_name}.png"
            if img_path.exists():
                with open(img_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return f"<div class='champ-img-box'><img src='data:image/png;base64,{encoded_string}' alt='{champ_name}'/></div>"
            return "<div class='champ-img-box'></div>"

        # Link dropdown changes to HTML visual updates
        t1_top.change(fn=update_champ_img, inputs=t1_top, outputs=img_t1_top)
        t1_jg.change(fn=update_champ_img, inputs=t1_jg, outputs=img_t1_jg)
        t1_mid.change(fn=update_champ_img, inputs=t1_mid, outputs=img_t1_mid)
        t1_adc.change(fn=update_champ_img, inputs=t1_adc, outputs=img_t1_adc)
        t1_sup.change(fn=update_champ_img, inputs=t1_sup, outputs=img_t1_sup)
        
        t2_top.change(fn=update_champ_img, inputs=t2_top, outputs=img_t2_top)
        t2_jg.change(fn=update_champ_img, inputs=t2_jg, outputs=img_t2_jg)
        t2_mid.change(fn=update_champ_img, inputs=t2_mid, outputs=img_t2_mid)
        t2_adc.change(fn=update_champ_img, inputs=t2_adc, outputs=img_t2_adc)
        t2_sup.change(fn=update_champ_img, inputs=t2_sup, outputs=img_t2_sup)

        # --- LÓGICA DE FUNCIONALIDADE ---
        btn_insights.click(
            fn=gerar_insights, 
            inputs=[
                dropdown_t1, dropdown_t2, dropdown_patches,
                t1_top, t1_jg, t1_mid, t1_adc, t1_sup,
                t2_top, t2_jg, t2_mid, t2_adc, t2_sup
            ], 
            outputs=insights_html
        )
        btn_pipeline.click(fn=executar_pipeline_completo, inputs=[], outputs=console_saida)

    return app, css
