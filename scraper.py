import re
import random
from datetime import datetime
import database

# Dicionários de Cidades e UFs comuns para suporte ao parser e geração
CIDADES_UF = {
    "Joinville": "SC",
    "Itajaí": "SC",
    "Blumenau": "SC",
    "Curitiba": "PR",
    "São José dos Pinhais": "PR",
    "Porto Alegre": "RS",
    "Caxias do Sul": "RS",
    "São Paulo": "SP",
    "Campinas": "SP",
    "Santos": "SP",
    "Belo Horizonte": "MG",
    "Uberlândia": "MG",
    "Rio de Janeiro": "RJ",
    "Duque de Caxias": "RJ",
    "Goiânia": "GO",
    "Brasília": "DF",
}

PRODUTOS = [
    ("Bobinas de Aço", 24.0, 3800),
    ("Alimentos Processados", 22.0, 3100),
    ("Peças Automotivas", 12.0, 2900),
    ("Tubos de PVC", 8.0, 2100),
    ("Carga Paletizada", 18.0, 3200),
    ("Madeira", 25.0, 4200),
    ("Material Plástico", 10.0, 2400),
    ("Fertilizantes", 23.5, 3900),
    ("Papel e Papelão", 14.0, 2800),
    ("Bebidas", 20.0, 3400)
]

VEICULOS = ["Carreta", "Truck", "Toco", "VLC"]
CARROCERIAS = ["Sider", "Baú", "Grade Baixa", "Prancha"]
EMPRESAS = ["TransLog", "Rapidão Sul", "RodoCarga", "Alfa Transportes", "LogBrasil", "Expresso Express", "Sul Vias"]

# Expressões Regulares para parsing
VEICULO_PATTERNS = {
    "Carreta": r"\b(carreta|carretas|bitrem|vanderleia|ls|eixos)\b",
    "Truck": r"\b(truck|6x2|trucado)\b",
    "Toco": r"\b(toco|3/4|toco)\b",
    "VLC": r"\b(vlc|vuc|hr|furgão)\b"
}

CARROCERIA_PATTERNS = {
    "Sider": r"\b(sider|siders)\b",
    "Baú": r"\b(bau|baú|gradeado)\b",
    "Grade Baixa": r"\b(grade baixa|graneleira|grade|aberta)\b",
    "Prancha": r"\b(prancha|plataforma)\b"
}

def parse_raw_message(text):
    """
    Varre um texto desestruturado usando Regex para extrair campos de carga.
    """
    text_lower = text.lower()
    
    # 1. Identificar Tipo de Veículo
    tipo_veiculo = "Carreta"  # Padrão
    for veiculo, pattern in VEICULO_PATTERNS.items():
        if re.search(pattern, text_lower):
            tipo_veiculo = veiculo
            break
            
    # 2. Identificar Tipo de Carroceria
    tipo_carroceria = "Sider"  # Padrão
    for carroceria, pattern in CARROCERIA_PATTERNS.items():
        if re.search(pattern, text_lower):
            tipo_carroceria = carroceria
            break

    # 3. Identificar Origem e Destino
    # Busca por padrões como "Joinville/SC x São Paulo/SP", "Curitiba-PR para Porto Alegre-RS", "JVE p/ SP"
    origem_cidade, origem_uf = "Joinville", "SC"
    destino_cidade, destino_uf = "São Paulo", "SP"
    
    # Procurar cidades conhecidas no texto
    cidades_encontradas = []
    for cidade, uf in CIDADES_UF.items():
        # Match exato da palavra da cidade ou abreviações comuns
        cidade_pat = rf"\b{re.escape(cidade.lower())}\b"
        if re.search(cidade_pat, text_lower):
            cidades_encontradas.append((cidade, uf, text_lower.find(cidade.lower())))
            
    # Se encontrar pelo menos duas cidades no texto, define origem e destino com base na ordem do texto
    if len(cidades_encontradas) >= 2:
        # Ordenar pela posição em que aparecem no texto para saber qual é origem e qual é destino
        cidades_encontradas.sort(key=lambda x: x[2])
        origem_cidade, origem_uf = cidades_encontradas[0][0], cidades_encontradas[0][1]
        destino_cidade, destino_uf = cidades_encontradas[1][0], cidades_encontradas[1][1]
    elif len(cidades_encontradas) == 1:
        # Se achou só uma, ela é a origem e o destino fica como padrão SP
        origem_cidade, origem_uf = cidades_encontradas[0][0], cidades_encontradas[0][1]
        if origem_cidade == "São Paulo":
            destino_cidade, destino_uf = "Joinville", "SC"
            
    # Caso não ache cidades por nome direto, tenta buscar por padrões de UF ex: "SC x SP" ou "PR p/ RS"
    # buscando a primeira e segunda ocorrência de UFs brasileiras
    ufs = re.findall(r"\b(SC|SP|PR|RS|RJ|MG|GO|DF)\b", text, re.IGNORECASE)
    if len(ufs) >= 2:
        # Se não encontramos cidades mas temos UFs, atualiza pelo menos as UFs
        # E define cidades padrão para esses estados
        origem_uf = ufs[0].upper()
        destino_uf = ufs[1].upper()
        # Encontra alguma cidade padrão para essas UFs
        origem_cidade = next((c for c, u in CIDADES_UF.items() if u == origem_uf), "Capital")
        destino_cidade = next((c for c, u in CIDADES_UF.items() if u == destino_uf), "Capital")

    # 4. Valor do Frete
    valor_frete = None
    # Procura por "R$ 3500", "paga 3800", "frete: 3000", "3.500"
    valor_match = re.search(r"(?:r\$|pago|paga|frete|valor)\s*[:\-=]?\s*(\d+(?:[\.,]\d{3})*(?:[\.,]\d{2})?)", text_lower)
    if valor_match:
        val_str = valor_match.group(1).replace(".", "").replace(",", ".")
        try:
            valor_frete = float(val_str)
        except ValueError:
            pass
    else:
        # Tenta pegar apenas números soltos de 3 ou 4 dígitos que possam ser o frete (ex: "paga 3500")
        numeros = re.findall(r"\b\d{4}\b", text_lower)
        if numeros:
            valor_frete = float(numeros[0])
            
    # 5. Peso em toneladas
    peso_ton = None
    # Procura por "24t", "12 tons", "8.5 toneladas", "24 ton"
    peso_match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:t|ton|tons|toneladas|tns)\b", text_lower)
    if peso_match:
        peso_str = peso_match.group(1).replace(",", ".")
        try:
            peso_ton = float(peso_str)
        except ValueError:
            pass
            
    # 6. Contato (Telefone/WhatsApp)
    contato_origem = "Contato no Canal"
    # Procura por DDD + número de celular ou fixo (ex: (47) 99999-9999, 47999999999, 11 98888-7777, etc.)
    contato_match = re.search(r"(\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4})", text)
    if contato_match:
        contato_origem = contato_match.group(1)
        
    # 7. Produto
    produto = "Diversos"
    # Se encontrar alguma correspondência de produto conhecido no texto
    for prod_name, _, _ in PRODUTOS:
        # Ex: "Bobinas", "Alimentos", "Tubos"
        palavra_chave = prod_name.split()[0].lower()
        if palavra_chave in text_lower:
            produto = prod_name
            break

    return {
        "data_captura": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "origem_cidade": origem_cidade,
        "origem_uf": origem_uf,
        "destino_cidade": destino_cidade,
        "destino_uf": destino_uf,
        "tipo_veiculo": tipo_veiculo,
        "tipo_carroceria": tipo_carroceria,
        "produto": produto,
        "peso_ton": peso_ton,
        "valor_frete": valor_frete,
        "contato_origem": contato_origem,
        "status_agenciamento": "Disponível"
    }

def generate_random_load_message():
    """
    Gera uma mensagem de carga fictícia em texto desestruturado (estilo WhatsApp)
    e retorna o texto original e o dicionário de campos extraído dela.
    """
    origem = random.choice(list(CIDADES_UF.keys()))
    origem_uf = CIDADES_UF[origem]
    
    # Evitar origem e destino iguais
    destino = random.choice([c for c in CIDADES_UF.keys() if c != origem])
    destino_uf = CIDADES_UF[destino]
    
    veiculo = random.choice(VEICULOS)
    carroceria = random.choice(CARROCERIAS)
    prod_info = random.choice(PRODUTOS)
    
    produto = prod_info[0]
    # Flutuação aleatória de peso e frete com base no produto
    peso = round(prod_info[1] * random.uniform(0.8, 1.2), 1)
    valor = int(prod_info[2] * random.uniform(0.9, 1.1))
    
    ddd = random.choice(["11", "47", "51", "41", "31", "21"])
    numero = f"9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}"
    contato = f"({ddd}) {numero}"
    empresa = random.choice(EMPRESAS)
    
    # Modelos de mensagens reais de WhatsApp
    templates = [
        "🚨 *OPORTUNIDADE DE FRETE* - {empresa}\n📍 Coleta: {origem}-{origem_uf}\n🏁 Entrega: {destino}-{destino_uf}\n🚚 Caminhão: {veiculo} {carroceria}\n📦 Carga: {produto} ({peso} ton)\n💵 Frete: R$ {valor} líquido\n📞 Contato: {contato}",
        "⚠️ Preciso URGENTE de {veiculo} {carroceria} para carregar {produto} de {origem}/{origem_uf} para {destino}/{destino_uf}. Peso {peso}t. Paga-se R$ {valor}. Ligar para {contato} falar c/ Expedição.",
        "Carga disponível: {origem}_{origem_uf} x {destino}_{destino_uf} | {veiculo} {carroceria} | Prod: {produto} {peso}t | Frete R$ {valor} | Fone {contato} ({empresa})",
        "[FRETE DIRETO] - {veiculo} {carroceria} em {origem} p/ {destino} - {produto} {peso} toneladas. Valor do Frete: {valor}. Contato: {contato}."
    ]
    
    msg_template = random.choice(templates)
    raw_message = msg_template.format(
        empresa=empresa,
        origem=origem,
        origem_uf=origem_uf,
        destino=destino,
        destino_uf=destino_uf,
        veiculo=veiculo.upper(),
        carroceria=carroceria.upper(),
        produto=produto,
        peso=peso,
        valor=valor,
        contato=contato
    )
    
    # Realiza o parsing dessa mensagem gerada
    parsed_data = parse_raw_message(raw_message)
    # Garante que os valores numéricos gerados sejam inseridos corretamente caso a regex falhe levemente
    if not parsed_data["valor_frete"]:
        parsed_data["valor_frete"] = float(valor)
    if not parsed_data["peso_ton"]:
        parsed_data["peso_ton"] = float(peso)
        
    return raw_message, parsed_data

def run_mock_scraping():
    """
    Simula o robô fazendo uma varredura: gera uma nova carga, realiza o parse e salva no banco.
    """
    raw_msg, parsed_data = generate_random_load_message()
    carga_id, is_new = database.save_carga(parsed_data)
    return {
        "raw_message": raw_msg,
        "parsed_data": parsed_data,
        "carga_id": carga_id,
        "is_new": is_new
    }
