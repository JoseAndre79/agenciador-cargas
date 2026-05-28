import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

import database
import scraper

app = FastAPI(title="Agenciador de Cargas API", version="1.0.0")

# Inicializa o banco de dados ao iniciar o servidor
@app.on_event("startup")
def startup_event():
    database.init_db()

# Modelos Pydantic para validação
class StatusUpdate(BaseModel):
    status: str

class MatchRequest(BaseModel):
    id_carga: int
    id_motorista: int

class ParseRequest(BaseModel):
    text: str

class ManualCargaInput(BaseModel):
    origem_cidade: str
    origem_uf: str
    destino_cidade: str
    destino_uf: str
    tipo_veiculo: str
    tipo_carroceria: str
    produto: str
    peso_ton: Optional[float] = None
    valor_frete: Optional[float] = None
    contato_origem: str

# Rotas da API
@app.get("/api/cargas")
def read_cargas(
    origem_uf: Optional[str] = None,
    destino_uf: Optional[str] = None,
    tipo_veiculo: Optional[str] = None,
    status: Optional[str] = None
):
    try:
        return database.get_cargas(origem_uf, destino_uf, tipo_veiculo, status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cargas/{id_carga}")
def read_carga(id_carga: int):
    carga = database.get_carga_by_id(id_carga)
    if not carga:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
    return carga

@app.post("/api/cargas/{id_carga}/status")
def update_status(id_carga: int, data: StatusUpdate):
    valid_statuses = ["Disponível", "Em Negociação", "Fechado", "Expirado"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    success = database.update_carga_status(id_carga, data.status)
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao atualizar status")
    return {"message": f"Status atualizado para {data.status} com sucesso"}

@app.get("/api/cargas/{id_carga}/motoristas")
def get_matching_drivers(id_carga: int):
    # Verifica se a carga existe
    carga = database.get_carga_by_id(id_carga)
    if not carga:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
        
    drivers = database.get_motoristas_for_carga(id_carga)
    return drivers

@app.post("/api/match")
def match_carga_motorista(data: MatchRequest):
    # Validar carga e motorista
    carga = database.get_carga_by_id(data.id_carga)
    if not carga:
        raise HTTPException(status_code=404, detail="Carga não encontrada")
        
    # Processar Match no banco
    success = database.process_match(data.id_carga, data.id_motorista)
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao registrar Match")
        
    # Obter telefone do motorista para formatar o disparo
    conn = database.get_db_connection()
    motorista = conn.execute("SELECT * FROM motoristas WHERE id_motorista = ?", (data.id_motorista,)).fetchone()
    conn.close()
    
    # Formata a mensagem padrão que seria disparada no WhatsApp
    msg_template = (
        f"🚚 *MATCH DE CARGA DE RETORNO!*\n"
        f"Olá {motorista['nome']},\n\n"
        f"Identificamos uma carga ideal para você que está em {motorista['cidade_atual']}-{motorista['uf_atual']}:\n"
        f"• *Origem*: {carga['origem_cidade']}-{carga['origem_uf']}\n"
        f"• *Destino*: {carga['destino_cidade']}-{carga['destino_uf']}\n"
        f"• *Caminhão*: {carga['tipo_veiculo']} {carga['tipo_carroceria']}\n"
        f"• *Produto*: {carga['produto']} ({carga['peso_ton']}t)\n"
        f"• *Valor*: R$ {carga['valor_frete']:.2f}\n"
        f"• *Contato*: {carga['contato_origem']}\n\n"
        f"Gostaria de carregar esta rota? Confirme aqui para que possamos emitir a sua Ordem de Carregamento!"
    )
    
    return {
        "success": True,
        "message": "Match realizado com sucesso",
        "dispatch_template": msg_template,
        "motorista_telefone": motorista['telefone']
    }

@app.post("/api/scraper/trigger")
def trigger_scraper():
    """
    Roda um ciclo do scraper simulado, adicionando uma nova carga no banco
    """
    try:
        result = scraper.run_mock_scraping()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scraper/parse-text")
def parse_and_insert_text(data: ParseRequest):
    """
    Recebe um texto colado (WhatsApp), roda o Regex parser e salva no banco
    """
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="O texto não pode ser vazio")
        
    try:
        parsed_data = scraper.parse_raw_message(data.text)
        carga_id, is_new = database.save_carga(parsed_data)
        return {
            "is_new": is_new,
            "carga_id": carga_id,
            "parsed_data": parsed_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cargas")
def create_carga_manually(data: ManualCargaInput):
    """
    Criação manual de uma carga
    """
    carga_dict = data.dict()
    try:
        carga_id, is_new = database.save_carga(carga_dict)
        if not is_new:
            return {"message": "Carga duplicada recente já existe no sistema", "id_carga": carga_id, "is_new": False}
        return {"message": "Carga criada com sucesso", "id_carga": carga_id, "is_new": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/motoristas")
def read_motoristas(status: Optional[str] = None):
    try:
        return database.get_motoristas(status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Servir o Frontend Estático
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Inicia o servidor na porta 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
