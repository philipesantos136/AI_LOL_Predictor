import gradio as gr
from interface.app import create_interface

if __name__ == "__main__":
    # 1. Cria a interface Gradio primeiro para obter as funções
    print("\n🖥️  Preparando Interface Web...")
    app, interface_css = create_interface()

    # 2. Executa o pipeline automaticamente antes de abrir a interface
    # (Usamos a função que já vem importada via interface.app no script)
    from interface.app import executar_pipeline_completo
    print("🚀 Iniciando Pipeline Automático...")
    resultado_pipeline = executar_pipeline_completo()
    print(resultado_pipeline)
    
    # 3. Inicia o app web com o tema e CSS conforme Gradio 6.0
    app.launch(theme=gr.themes.Soft(), css=interface_css)
