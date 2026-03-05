import gradio as gr
import sqlite3
import os
import sys
import importlib

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

def get_times_disponiveis():
    """Busca a lista de times únicos na tabela Silver para preencher os Dropdowns."""
    db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lol_datamatches.db"))
    if not os.path.exists(db_file):
        return ["Rode o Pipeline Primeiro"]
        
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT teamname FROM match_data_silver WHERE teamname IS NOT NULL ORDER BY teamname")
            times = [row[0] for row in cursor.fetchall()]
            return times if times else ["Nenhum time encontrado"]
    except Exception:
        return ["Erro ao carregar times"]

def get_patches_disponiveis():
    """Busca a lista de patches únicos na tabela Silver."""
    db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lol_datamatches.db"))
    if not os.path.exists(db_file):
        return ["Todos"]
        
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT patch FROM match_data_silver WHERE patch IS NOT NULL ORDER BY patch DESC")
            patches = [row[0] for row in cursor.fetchall()]
            return ["Todos"] + patches
    except Exception:
        return ["Todos"]

def executar_pipeline_completo():
    """Executa todas as etapas de ingestão e preparação de dados em sequência."""
    log = ""
    try:
        log += "⏳ Iniciando Download do CSV (Google Drive)...\n"
        baixar_arquivo_mais_recente()
        log += "✅ Download Concluído!\n\n"
        
        log += "⏳ Criando/Populando Tabela Bronze (SQLite)...\n"
        csv_to_sqlite()
        log += "✅ Bronze OK!\n\n"
        
        log += "⏳ Criando Estrutura da Tabela Silver...\n"
        criar_tabela_silver()
        log += "✅ Silver Estrutura OK!\n\n"
        
        log += "⏳ Inserindo Dados na Tabela Silver...\n"
        popular_tabela_silver()
        log += "✅ Silver Dados OK!\n\n"
        
        log += "🎉 PARABÉNS! Pipeline concluído com sucesso. A base de dados está atualizada e pronta para predições."
        return log
    except Exception as e:
        return f"❌ ERRO DURANTE O PIPELINE: {str(e)}\n\nVerifique os arquivos originais e a conexão de rede."

def prever_partida(time1, time2, patches):
    """Aciona o Gemini para analisar os dois times informados."""
    if not time1 or not time2 or time1 == "Rode o Pipeline Primeiro" or time2 == "Rode o Pipeline Primeiro":
        return "⚠️ Por favor, atualize o pipeline e selecione dois times válidos primeiro."
    if time1 == time2:
        return "⚠️ Por favor, selecione times diferentes."
        
    try:
        return dsa_gera_analises(time1, time2, patches)
    except Exception as e:
        return f"❌ ERRO NA PREDIÇÃO: {str(e)}"

def atualizar_dropdowns():
    """Atualiza a lista de times e patches nos dropdowns."""
    times = get_times_disponiveis()
    patches = get_patches_disponiveis()
    return gr.update(choices=times), gr.update(choices=times), gr.update(choices=patches)

def create_interface():
    # --- CSS PERSONALIZADO ---
    css = """
    .sidebar-menu-btn {
        text-align: left !important;
        justify-content: flex-start !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.3s ease !important;
        padding: 10px 15px !important;
    }
    .sidebar-menu-btn:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(5px);
    }
    .sidebar-active {
        background: rgba(255, 255, 255, 0.2) !important;
        border-left: 4px solid #fff !important;
    }
    .glass-container {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px !important;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .caixa-resultado {
        min-height: 200px;
        border: 1px solid #444;
        padding: 15px;
        background: #111;
        border-radius: 8px;
    }
    /* Animação de entrada */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .view-content {
        animation: fadeIn 0.5s ease forwards;
    }
    """

    with gr.Blocks(title="LoL e-Sports Predictor AI", theme=gr.themes.Default(primary_hue="blue", secondary_hue="slate"), css=css) as app:
        
        # Estado para controlar qual menu está ativo
        current_view = gr.State("predicao")

        with gr.Sidebar(label="LoL Predictor Menu") as sidebar:
            gr.Markdown("## 🎮 NAVEGAÇÃO")
            btn_menu_predicao = gr.Button("🏆 Vencedor da Partida", elem_classes=["sidebar-menu-btn", "sidebar-active"])
            btn_menu_pipeline = gr.Button("⚙️ Engenharia de Dados", elem_classes="sidebar-menu-btn")
            
            gr.Markdown("---")
            gr.Markdown("Powered by **Gemini 2.0 Flash**\nLocal Stats Database")
            
        # Conteúdo Principal
        with gr.Column(elem_classes="view-content"):
            
            # --- SEÇÃO 1: VENCEDOR DA PARTIDA ---
            with gr.Group(visible=True) as group_predicao:
                gr.Markdown("# 🏆 Análise de Vencedor", elem_classes="main-header")
                
                with gr.Row(elem_classes="glass-container"):
                    with gr.Column():
                        times_iniciais = get_times_disponiveis()
                        patches_iniciais = get_patches_disponiveis()
                        
                        with gr.Row():
                            dropdown_t1 = gr.Dropdown(choices=times_iniciais, label="🟦 Time 1 (Blue Side)", allow_custom_value=True)
                            dropdown_t2 = gr.Dropdown(choices=times_iniciais, label="🟥 Time 2 (Red Side)", allow_custom_value=True)
                        
                        dropdown_patches = gr.Dropdown(choices=patches_iniciais, value=["Todos"], multiselect=True, label="📅 Versão do Patch")
                        
                        with gr.Row():
                            btn_prever = gr.Button("🔮 Gerar Predição", variant="primary")
                            btn_atualizar_times = gr.Button("🔄 Atualizar Dados", size="sm")

                gr.Markdown("### 📝 Relatório de Inteligência")
                resultado_markdown = gr.Markdown("Selecione os times e clique em prever...", elem_classes="caixa-resultado")

            # --- SEÇÃO 2: PIPELINE ---
            with gr.Group(visible=False) as group_pipeline:
                gr.Markdown("# ⚙️ Engenharia de Dados", elem_classes="main-header")
                
                with gr.Column(elem_classes="glass-container"):
                    gr.Markdown("Clique no botão abaixo para baixar os dados mais recentes do Google Drive e atualizar sua base local (Bronze & Silver).")
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

        # --- LÓGICA DE FUNCIONALIDADE ---
        btn_prever.click(fn=prever_partida, inputs=[dropdown_t1, dropdown_t2, dropdown_patches], outputs=resultado_markdown)
        btn_atualizar_times.click(fn=atualizar_dropdowns, inputs=[], outputs=[dropdown_t1, dropdown_t2, dropdown_patches])
        btn_pipeline.click(fn=executar_pipeline_completo, inputs=[], outputs=console_saida)

    return app
