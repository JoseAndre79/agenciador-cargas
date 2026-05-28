import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cargas.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Criar tabela de cargas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cargas (
        id_carga INTEGER PRIMARY KEY AUTOINCREMENT,
        data_captura TEXT NOT NULL,
        origem_cidade TEXT NOT NULL,
        origem_uf TEXT NOT NULL,
        destino_cidade TEXT NOT NULL,
        destino_uf TEXT NOT NULL,
        tipo_veiculo TEXT NOT NULL,
        tipo_carroceria TEXT NOT NULL,
        produto TEXT NOT NULL,
        peso_ton REAL,
        valor_frete REAL,
        contato_origem TEXT NOT NULL,
        status_agenciamento TEXT NOT NULL DEFAULT 'Disponível'
    )
    """)
    
    # Criar tabela de motoristas para simular o "Match"
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS motoristas (
        id_motorista INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        cidade_atual TEXT NOT NULL,
        uf_atual TEXT NOT NULL,
        tipo_veiculo TEXT NOT NULL,
        tipo_carroceria TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Disponível'
    )
    """)
    
    # Inserir alguns motoristas fictícios se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM motoristas")
    if cursor.fetchone()[0] == 0:
        motoristas_mock = [
            ("João Silva (Bitrem)", "(11) 98888-1111", "Joinville", "SC", "Carreta", "Sider", "Disponível"),
            ("Pedro Santos", "(47) 97777-2222", "Itajaí", "SC", "Carreta", "Baú", "Disponível"),
            ("Marcos Oliveira", "(51) 96666-3333", "Porto Alegre", "RS", "Truck", "Baú", "Disponível"),
            ("Carlos Souza", "(41) 95555-4444", "Curitiba", "PR", "Carreta", "Sider", "Disponível"),
            ("Lucas Lima", "(19) 94444-5555", "Campinas", "SP", "Truck", "Sider", "Disponível"),
            ("Antônio Rocha", "(31) 93333-6666", "Belo Horizonte", "MG", "Toco", "Grade Baixa", "Disponível"),
            ("Felipe Dias", "(62) 92222-7777", "Goiânia", "GO", "VLC", "Baú", "Disponível"),
        ]
        cursor.executemany("""
        INSERT INTO motoristas (nome, telefone, cidade_atual, uf_atual, tipo_veiculo, tipo_carroceria, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, motoristas_mock)
        
    # Inserir algumas cargas mock de exemplo se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM cargas")
    if cursor.fetchone()[0] == 0:
        cargas_mock = [
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Joinville", "SC", "São Paulo", "SP", "Carreta", "Sider", "Bobinas de Aço", 24.5, 3800.00, "(47) 3451-9900 / TransJoinville", "Disponível"),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Curitiba", "PR", "Porto Alegre", "RS", "Carreta", "Sider", "Alimentos Processados", 22.0, 3100.00, "(41) 3222-8888 / LogSul", "Disponível"),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Caxias do Sul", "RS", "Campinas", "SP", "Truck", "Baú", "Peças Automotivas", 12.0, 2900.00, "(54) 3025-1122 / ExpressRS", "Disponível"),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Belo Horizonte", "MG", "Rio de Janeiro", "RJ", "Toco", "Grade Baixa", "Tubos de PVC", 6.5, 1800.00, "(31) 3344-5566 / TubosLog", "Disponível"),
        ]
        cursor.executemany("""
        INSERT INTO cargas (data_captura, origem_cidade, origem_uf, destino_cidade, destino_uf, tipo_veiculo, tipo_carroceria, produto, peso_ton, valor_frete, contato_origem, status_agenciamento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cargas_mock)
        
    conn.commit()
    conn.close()

def get_cargas(origem_uf=None, destino_uf=None, tipo_veiculo=None, status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM cargas WHERE 1=1"
    params = []
    
    if origem_uf:
        query += " AND origem_uf = ?"
        params.append(origem_uf)
    if destino_uf:
        query += " AND destino_uf = ?"
        params.append(destino_uf)
    if tipo_veiculo:
        query += " AND tipo_veiculo = ?"
        params.append(tipo_veiculo)
    if status:
        query += " AND status_agenciamento = ?"
        params.append(status)
        
    query += " ORDER BY id_carga DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_carga_by_id(id_carga):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cargas WHERE id_carga = ?", (id_carga,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_carga(carga_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # De-duplicação: Verificar se já existe uma carga idêntica criada nas últimas 3 horas
    # Chaves: origem, destino, tipo_veiculo, tipo_carroceria, produto
    # E que não esteja expirada ou fechada
    cursor.execute("""
    SELECT id_carga FROM cargas 
    WHERE origem_cidade = ? AND origem_uf = ? 
      AND destino_cidade = ? AND destino_uf = ? 
      AND tipo_veiculo = ? AND tipo_carroceria = ?
      AND status_agenciamento NOT IN ('Fechado', 'Expirado')
      AND datetime(data_captura) >= datetime('now', '-3 hour')
    """, (
        carga_dict['origem_cidade'], carga_dict['origem_uf'],
        carga_dict['destino_cidade'], carga_dict['destino_uf'],
        carga_dict['tipo_veiculo'], carga_dict['tipo_carroceria']
    ))
    
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing[0], False  # Retorna ID existente, False indica que não foi inserida nova
        
    # Inserir nova carga
    data_cap = carga_dict.get('data_captura') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO cargas (data_captura, origem_cidade, origem_uf, destino_cidade, destino_uf, tipo_veiculo, tipo_carroceria, produto, peso_ton, valor_frete, contato_origem, status_agenciamento)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_cap,
        carga_dict['origem_cidade'],
        carga_dict['origem_uf'],
        carga_dict['destino_cidade'],
        carga_dict['destino_uf'],
        carga_dict['tipo_veiculo'],
        carga_dict['tipo_carroceria'],
        carga_dict['produto'],
        carga_dict.get('peso_ton'),
        carga_dict.get('valor_frete'),
        carga_dict['contato_origem'],
        carga_dict.get('status_agenciamento', 'Disponível')
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id, True

def update_carga_status(id_carga, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE cargas SET status_agenciamento = ? WHERE id_carga = ?
    """, (status, id_carga))
    conn.commit()
    conn.close()
    return True

def get_motoristas(status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM motoristas WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_motoristas_for_carga(id_carga):
    carga = get_carga_by_id(id_carga)
    if not carga:
        return []
        
    conn = get_db_connection()
    cursor = conn.cursor()
    # Match inteligente: motoristas disponíveis que tenham o mesmo tipo de veículo e tipo de carroceria
    cursor.execute("""
    SELECT * FROM motoristas 
    WHERE status = 'Disponível'
      AND tipo_veiculo = ? 
      AND tipo_carroceria = ?
    """, (carga['tipo_veiculo'], carga['tipo_carroceria']))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def process_match(id_carga, id_motorista):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Atualizar carga para fechada
    cursor.execute("UPDATE cargas SET status_agenciamento = 'Fechado' WHERE id_carga = ?", (id_carga,))
    # Atualizar motorista para Carregado
    cursor.execute("UPDATE motoristas SET status = 'Carregado' WHERE id_motorista = ?", (id_motorista,))
    
    conn.commit()
    conn.close()
    return True
