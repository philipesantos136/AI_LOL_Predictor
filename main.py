import sys
from pipeline.controller import executar_pipeline_completo

if __name__ == "__main__":
    # Impede a criação de arquivos __pycache__ e .pyc
    sys.dont_write_bytecode = True
    
    print("🚀 Iniciando Pipeline Automático de Processamento de Dados...")
    resultado_pipeline = executar_pipeline_completo()
    print(resultado_pipeline)
    
    print("\n✅ Pipeline concluído. Para iniciar a interface visual:")
    print("1. Inicie o backend: python api.py")
    print("2. Inicie o frontend: cd frontend && npm run dev")
