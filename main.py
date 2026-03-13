import sys
import subprocess
import os
import time
from pipeline.controller import executar_pipeline_completo

def run_servers():
    """Lança o backend (FastAPI) e o frontend (SvelteKit) em subprocessos e os mantém rodando."""
    print("\n🌐 Iniciando os servidores da Aplicação (Backend & Frontend)...")
    
    # 1. Inicia o Backend Python (FastAPI via Uvicorn)
    # Assumimos que o comando python atual (sys.executable) seja usado para garantir o mesmo ambiente virtual
    backend_process = subprocess.Popen(
        [sys.executable, "api.py"],
        cwd=os.getcwd(),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Dá um tempo pro backend subir
    time.sleep(2)
    
    # 2. Inicia o Frontend SvelteKit (via npm)
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    
    # No Windows, o shell=True é geralmente necessário para comandos npm
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    print("\n✅ Aplicação rodando!")
    print("👉 Acesse o Frontend em: http://localhost:5173")
    print("👉 A API está rodando em: http://localhost:8000")
    print("\nPressione Ctrl+C para encerrar todos os servidores.")
    
    try:
        # Aguarda infinitamente até que os processos sejam interrompidos ou encerrem
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando servidores...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Servidores encerrados com sucesso.")

if __name__ == "__main__":
    # Impede a criação de arquivos __pycache__ e .pyc
    sys.dont_write_bytecode = True
    
    print("🚀 Iniciando Pipeline Automático de Processamento de Dados...")
    resultado_pipeline = executar_pipeline_completo()
    print(resultado_pipeline)
    
    # Inicia os servidores Web e de API simultaneamente
    run_servers()
