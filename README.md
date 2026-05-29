# Projeto Agenciador de Cargas Inteligente (MVP)
## Sistema Automatizado de Captação, Triagem e Distribuição de Fretes

Este documento apresenta o escopo técnico e operacional detalhado para a implementação do projeto de agenciamento de cargas. O foco central desta primeira fase (MVP) é resolver o maior desafio do negócio: **a captação, centralização e filtragem inteligente de cargas em todo o Brasil**, permitindo que a operação funcione inicialmente como um serviço de informação de alto valor para motoristas, monetizado por meio de comissões de agenciamento junto aos embarcadores/transportadoras.

---

## 1. Visão Geral do Fluxo da Operação

O sistema opera em um ciclo contínuo de quatro etapas para garantir que a informação chegue tratada e em tempo real para os motoristas, maximizando as chances de match e fechamento de frete.

```
[ CAPTAÇÃO (Inputs) ]
  ├── Portais Públicos / Sites de Transportadoras
  ├── Grupos de Logística (WhatsApp/Telegram)
  └── Parcerias Diretas (Cargas de Retorno)
            │
            ▼
[ ENGENHARIA DE TRIAGEM (Python / Automação) ]
  ├── Extração de Dados (Playwright/Selenium)
  ├── Normalização (Limpeza de duplicadas, Regex de Texto)
  └── Filtro por Regras de Negócio (Tipos de veículo, rotas de liquidez)
            │
            ▼
[ BANCO DE DADOS CENTRAL (Estrutura) ]
  └── Armazenamento e Histórico de Status (Disponível, Negociando, Fechado)
            │
            ▼
[ DISTRIBUIÇÃO E MONETIZAÇÃO (Outputs) ]
  ├── Disparos Segmentados (Telegram/WhatsApp por Região/Carroceria)
  └── Abordagem Comercial (Garantia de comissão com Embarcador)
```

---

## 2. Estrutura de Dados (Modelo do Banco de Dados)

Para que a automação e a triagem funcionem perfeitamente, todas as cargas captadas devem ser normalizadas seguindo a estrutura de campos abaixo. Esta tabela pode ser implementada inicialmente em um banco de dados leve (como SQLite) ou integrada via APIs.

| Campo | Tipo | Descrição | Exemplo / Regra |
| :--- | :--- | :--- | :--- |
| `id_carga` | UUID / INT | Identificador único gerado pelo sistema | `1024` |
| `data_captura` | TIMESTAMP | Data e hora em que a carga foi identificada | `2026-05-28 13:20:00` |
| `origem_cidade` | VARCHAR | Cidade de origem da coleta | `Joinville` |
| `origem_uf` | VARCHAR(2) | Estado de origem | `SC` |
| `destino_cidade` | VARCHAR | Cidade final de entrega | `São Paulo` |
| `destino_uf` | VARCHAR(2) | Estado de destino | `SP` |
| `tipo_veiculo` | VARCHAR | Tipo de caminhão exigido | `Carreta`, `Truck`, `Toco`, `VLC` |
| `tipo_carroceria` | VARCHAR | Tipo de carroceria necessária | `Sider`, `Baú`, `Grade Baixa`, `Prancha` |
| `produto` | VARCHAR | Tipo de mercadoria transportada | `Bobinas`, `Alimentos`, `Metalúrgico` |
| `peso_ton` | DECIMAL | Peso da carga em toneladas | `24.5` |
| `valor_frete` | DECIMAL | Valor ofertado (Bruto ou Líquido) | `3500.00` |
| `contato_origem` | VARCHAR | Link, telefone ou email de quem postou | `(11) 99999-9999 / Transportadora X` |
| `status_agenciamento`| ENUM | Status atual da oportunidade no sistema | `Disponível`, `Em Negociação`, `Fechado`, `Expirado` |

---

## 3. Arquitetura Técnica do Robô de Captação (Python)

Para vencer o desafio de encontrar cargas, a arquitetura do script de automação deve ser dividida em módulos específicos, utilizando bibliotecas robustas para evitar bloqueios e garantir velocidade.

### Módulos do Script:
1. **Módulo de Navegação (`Scraper Engine`):** Utilização do **Playwright** ou **Selenium** rodando em modo *headless* para acessar painéis de fretes, páginas de transportadoras e murais públicos.
2. **Módulo de Parsing (`Data Extractor`):** Utilização de Expressões Regulares (`re` em Python) para varrer textos não estruturados (comum em postagens de grupos) e extrair palavras-chave como "Origem:", "Destino:", "Paga-se", além de identificar números de telefone de contato.
3. **Módulo de Higienização (`De-duplication`):** Tratamento dos dados capturados. Se a mesma carga foi postada com variações de texto pela mesma empresa, o sistema faz o cruzamento pelas chaves `[origem_cidade] + [destino_cidade] + [tipo_veiculo]` dentro de uma janela de 3 horas para evitar duplicidade.

---

## 4. Estratégia Comercial e Operacional de Agenciamento

A captação técnica resolve o problema de encontrar a oportunidade, mas o ganho da comissão depende da execução operacional. O fluxo abaixo detalha como transformar a informação em receita:

### Fluxo do Match Rentável:
* **Passo 1 (Alerta Interno):** O robô identifica uma carga de alta liquidez (Ex: Origem em polo industrial como Joinville/SC, Curitiba/PR ou Porto Alegre/RS).
* **Passo 2 (Bloqueio da Carga):** Você entra em contato com o responsável pela postagem (transportadora parceira):
  > *"Olá, vi sua demanda de Joinville para São Paulo para Carreta Sider. Temos veículos da nossa base fidelizada operando nessa rota agora. Podemos fechar o agenciamento? Você trabalha com taxa de cadastro ou comissão retida no manifesto?"*
* **Passo 3 (Distribuição Segmentada):** Assim que a carga está assegurada pelo agenciamento, o sistema dispara a informação formatada para os motoristas nos canais específicos.
* **Passo 4 (Faturamento):** O motorista aceita, realiza a coleta e você recebe a comissão acordada junto à transportadora contratante ou retém a margem acordada direto no repasse do frete.

---

## 5. Próximos Passos para Implementação no AntiGravity

Para iniciar a codificação das automações dentro do ambiente de desenvolvimento, seguiremos a seguinte ordem de sprints:

1. **Configuração do Ambiente:** Instalação das dependências (`playwright`, `pandas`, `sqlite3`).
2. **Desenvolvimento do Scraper Piloto:** Escolha de 2 portais públicos ou páginas de transportadoras expressivas para mapear as tags HTML e criar as primeiras regras de extração de texto.
3. **Módulo de Formatação de Mensagens:** Criar a rotina que pega a linha do banco de dados e gera o texto padrão estruturado para envio automatizado para as redes de motoristas.
