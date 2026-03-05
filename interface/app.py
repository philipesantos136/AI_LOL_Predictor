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
    """

    with gr.Blocks(title="LoL e-Sports Predictor AI") as app:
        # Armazena o CSS em um componente invísivel para o main.py ler se necessário, 
        # ou apenas retornamos ele na função create_interface acompanhando o app
        
        # Estado para controlar qual menu está ativo
        current_view = gr.State("predicao")

        with gr.Sidebar(label="LoL Predictor Menu") as sidebar:
            gr.Markdown("## 🎮 NAVEGAÇÃO")
            btn_menu_predicao = gr.Button("🏆 Vencedor da Partida", elem_classes=["sidebar-menu-btn", "sidebar-active"])
            btn_menu_pipeline = gr.Button("⚙️ Engenharia de Dados", elem_classes="sidebar-menu-btn")
            
            gr.Markdown("---")
            gr.Markdown("Powered by **Gemini 2.0 Flash**\nLocal Stats Database")
            
        # Conteúdo Principal
        with gr.Column():
            
            # --- SEÇÃO 1: VENCEDOR DA PARTIDA ---
            with gr.Group(visible=True) as group_predicao:
                gr.Markdown("# 🏆 Análise de Vencedor", elem_classes="main-title")
                
                with gr.Column(elem_classes="container-boxed"):
                    times_originais = get_times_disponiveis()
                    patches_originais = get_patches_disponiveis()
                    
                    with gr.Row():
                        dropdown_t1 = gr.Dropdown(choices=times_originais, label="🟦 Time 1 (Blue Side)", allow_custom_value=True)
                        dropdown_t2 = gr.Dropdown(choices=times_originais, label="🟥 Time 2 (Red Side)", allow_custom_value=True)
                    
                    dropdown_patches = gr.Dropdown(
                        choices=patches_originais, 
                        value=["Todos"], 
                        multiselect=True, 
                        label="📅 Versão do Patch",
                        interactive=True
                    )
                    
                    with gr.Row():
                        btn_prever = gr.Button("🔮 Gerar Predição", variant="primary")
                        btn_atualizar_times = gr.Button("🔄 Atualizar Dados")

                gr.Markdown("### 📝 Relatório de Inteligência")
                resultado_markdown = gr.Markdown("Selecione os times e clique em prever...", elem_classes="caixa-resultado")

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

        # --- LÓGICA DE FUNCIONALIDADE ---
        btn_prever.click(fn=prever_partida, inputs=[dropdown_t1, dropdown_t2, dropdown_patches], outputs=resultado_markdown)
        btn_atualizar_times.click(fn=atualizar_dropdowns, inputs=[], outputs=[dropdown_t1, dropdown_t2, dropdown_patches])
        btn_pipeline.click(fn=executar_pipeline_completo, inputs=[], outputs=console_saida)

    return app, css
