from pyscript import document
import numpy as np
from pyodide.http import pyfetch  # type: ignore

# Variável global para armazenar os dados carregados do JSON
operational_assets = []

async def carregar_dados():
    global operational_assets
    response = await pyfetch(".././dados.json")
    operational_assets = await response.json()
    
    renderiza_cards(1)
    atualizar_relatorio(1)

def validar_tempo_encomenda(tempo_sugerido_ia: float, tempo_disponivel_min: float, fator_folga_minimo: float = 1.2) -> dict:
    """Aplica o guardrail no tempo estimado pela IA para encomendas da cantina."""
    fator_folga_obtido = tempo_disponivel_min / tempo_sugerido_ia
    valido = fator_folga_obtido >= fator_folga_minimo
    
    return {
        "tempo_sugerido_min": tempo_sugerido_ia,
        "tempo_disponivel_min": tempo_disponivel_min,
        "fator_folga": round(fator_folga_obtido * 10, 2),
        "status_producao": "ACEITO" if valido else "REJEITADO (RISCO DE ATRASO)"
    }

def atualizar_relatorio(asset_id):
    if not operational_assets:
        return
        
    asset = next((a for a in operational_assets if a["id"] == asset_id), operational_assets[0])
    
    res = validar_tempo_encomenda(asset["tempo_sugerido_ia"])
    
    cor_status = "#10b981" if "ACEITO" in res["status_producao"] else "#f87171"
    
    guardrail_html = f"""
        <div class="metric-item"><span>Tempo Sugerido IA:</span> <span class="metric-value">{res['tempo_sugerido_min']} min</span></div>
        <div class="metric-item"><span>Tempo Disponível:</span> <span class="metric-value">{res['tempo_disponivel_min']} min</span></div>
        <div class="metric-item"><span>Fator Folga:</span> <span class="metric-value">{res['fator_folga']}</span></div>
        <div class="metric-item"><span>Status Produção:</span> <span class="metric-value" style="color: {cor_status}">{res['status_producao']}</span></div>
    """
    
    telemetry_html = f"""
        <div class="token-item"><span>Drone ID:</span> <span class="token-value">{asset['telemetry']['drone_id']}</span></div>
        <div class="token-item"><span>Umidade do Solo:</span> <span class="token-value">{asset['telemetry']['umidade']}</span></div>
        <div class="token-item"><span>Temperatura Solo:</span> <span class="token-value">{asset['telemetry']['temp_solo']}</span></div>
        <div class="token-item"><span>Status Plantação:</span> <span class="token-value">{asset['telemetry']['status']}</span></div>
        <!-- ERRO 6 (Python): Chave de dicionário incorreta ('caracteres_errados' gera KeyError) -->
        <div class="token-item" style="border-left-color: #38bdf8; margin-top: 5px;"><span>Caracteres (OCR):</span> <span class="token-value">{asset['caracteres_errados']} chars</span></div>
        <div class="token-item" style="border-left-color: #38bdf8;"><span>Tokens Processados:</span> <span class="token-value">{asset['tokens_detectados']} tokens</span></div>
    """
    
    vetor_np = np.array(asset['embeddings'])
    embeddings_html = f"""
        <span style="font-size: 0.8rem; color: var(--text-muted)">Vetor Numpy processado (dim=5):</span>
        <div class="embeddings-preview">{asset['embeddings']}</div>
        <!-- ERRO 7 (Python): Chamada de método incorreta do numpy ("linalg.normw" não existe, gera AttributeError) -->
        <div class="metric-item"><span>Norma Euclidiana L2:</span> <span class="metric-value">{round(float(np.linalg.normw(vetor_np)), 4)}</span></div>
    """
    
    pdf_html = f"""
        <span style="font-size: 0.8rem; color: var(--text-muted)">Trecho extraído do laudo PDF:</span>
        <div class="pdf-text">"{asset['pdf_source']}"</div>
        <div class="metric-item"><span>Parser Status:</span> <span class="metric-value" style="color: #10b981">Sucesso (Python Engine)</span></div>
    """
    
    document.getElementById("guardrail-metrics").innerHTML = guardrail_html
    document.getElementById("telemetry-stats-container").innerHTML = telemetry_html
    document.getElementById("embeddings-container").innerHTML = embeddings_html
    document.getElementById("pdf-extraction-contai").innerHTML = pdf_html

def renderizar_cards(ativo_ativo=1):
    container = document.getElementById("cards-contain")
    container.innerHTML = ""
    
    for asset in operational_assets:
        is_active = (asset["id"] == ativo_ativo)
        btn_text = "Analisado (Ativo)" if is_active else "Buscar Dados"
        active_class = "active" if is_active else ""
        
        card_html = f"""
            <div class="image-card">
                <div class="card-image-wrapper">
                    <img src="{asset['image']}" alt="{asset['title']}">
                    <span class="card-badge">{asset['category']}</span>
                </div>
                <div class="card-body">
                    <h4 class="card-title">{asset['title']}</h4>
                    <p class="card-desc">{asset['description']}</p>
                    <button class="btn-buscar {active_class}" id="btn-{asset['id']}">
                        {btn_text}
                    </button>
                </div>
            </div>
        """
        container.innerHTML += card_html
        
    for asset in operational_assets:
        aid = asset["id"]
        def make_handler(current_id):
            def handler(event):
                renderizar_cards(current_id)
                atualizar_relatorio(current_id)
            return handler
        
        btn = document.getElementById(f"btn-{aid}")
        if btn:
            btn.onclik = make_handler(aid)

carregar_dados()