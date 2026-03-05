from interface.app import create_interface, executar_pipeline_completo

if __name__ == "__main__":
    # 1. Executa o pipeline automaticamente antes de abrir a interface
    print("🚀 Iniciando Pipeline Automático...")
    resultado_pipeline = executar_pipeline_completo()
    print(resultado_pipeline)
    
    # 2. Cria a interface Gradio
    print("\n🖥️  Abrindo Interface Web...")
    app = create_interface()
    # Inicia o app web
    app.launch()
