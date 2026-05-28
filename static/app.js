document.addEventListener("DOMContentLoaded", () => {
    // Referências DOM - Navegação
    const btnMenuDashboard = document.getElementById("btn-menu-dashboard");
    const btnMenuParser = document.getElementById("btn-menu-parser");
    const dashboardView = document.getElementById("dashboard-view");
    const parserView = document.getElementById("parser-view");
    const pageTitle = document.getElementById("page-title");
    
    // Referências DOM - Filtros
    const filterOrigemUf = document.getElementById("filter-origem-uf");
    const filterDestinoUf = document.getElementById("filter-destino-uf");
    const filterVeiculo = document.getElementById("filter-veiculo");
    const filterStatus = document.getElementById("filter-status");
    
    // Referências DOM - Cargas
    const cargasList = document.getElementById("cargas-list");
    const scrapeTriggerBtn = document.getElementById("btn-scrape-trigger");
    const refreshIndicator = document.getElementById("refresh-indicator");
    
    // Referências DOM - Detalhes
    const detailsPanel = document.getElementById("details-panel");
    const emptyDetails = document.getElementById("empty-details");
    const detailsContent = document.getElementById("details-content");
    const detailStatus = document.getElementById("detail-status");
    const detailRoute = document.getElementById("detail-route");
    const detailTime = document.getElementById("detail-time");
    const detailProduto = document.getElementById("detail-produto");
    const detailPeso = document.getElementById("detail-peso");
    const detailVeiculo = document.getElementById("detail-veiculo");
    const detailCarroceria = document.getElementById("detail-carroceria");
    const detailValor = document.getElementById("detail-valor");
    const detailContato = document.getElementById("detail-contato");
    
    const btnActionNegotiate = document.getElementById("btn-action-negotiate");
    const btnActionExpire = document.getElementById("btn-action-expire");
    const driversMatchList = document.getElementById("drivers-match-list");
    const matchCount = document.getElementById("match-count");
    
    // Referências DOM - Parser Sandbox
    const rawTextInput = document.getElementById("raw-text-input");
    const btnParseSubmit = document.getElementById("btn-parse-submit");
    const parserResultCard = document.getElementById("parser-result-card");
    const parsedOutputGrid = document.getElementById("parsed-output-grid");
    const terminalLogBody = document.getElementById("terminal-log-body");
    
    // Referências DOM - Modal Match
    const matchModal = document.getElementById("match-modal");
    const matchMessageText = document.getElementById("match-message-text");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnModalCancel = document.getElementById("btn-modal-cancel");
    const btnCopyMsg = document.getElementById("btn-copy-msg");
    const btnModalSendWhatsapp = document.getElementById("btn-modal-send-whatsapp");

    // Estado local da aplicação
    let state = {
        cargas: [],
        selectedCargaId: null,
        activeView: "dashboard", // "dashboard" ou "parser"
        activeMatch: null // guarda infos do match atual
    };

    // ==========================================
    // SISTEMA DE NAVEGAÇÃO
    // ==========================================
    function switchView(viewName) {
        state.activeView = viewName;
        if (viewName === "dashboard") {
            btnMenuDashboard.classList.add("active");
            btnMenuParser.classList.remove("active");
            dashboardView.classList.remove("hidden");
            parserView.classList.add("hidden");
            pageTitle.innerText = "Painel de Controle";
            loadCargas(); // Recarrega cargas ao voltar pro painel
        } else {
            btnMenuDashboard.classList.remove("active");
            btnMenuParser.classList.add("active");
            dashboardView.classList.add("hidden");
            parserView.classList.remove("hidden");
            pageTitle.innerText = "Triagem Inteligente (Sandbox)";
        }
    }

    btnMenuDashboard.addEventListener("click", (e) => {
        e.preventDefault();
        switchView("dashboard");
    });

    btnMenuParser.addEventListener("click", (e) => {
        e.preventDefault();
        switchView("parser");
    });

    // ==========================================
    // CARREGAMENTO E RENDERIZAÇÃO DE DADOS
    // ==========================================
    async function loadCargas() {
        refreshIndicator.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i> Sincronizando...';
        
        const oUf = filterOrigemUf.value;
        const dUf = filterDestinoUf.value;
        const veic = filterVeiculo.value;
        const stat = filterStatus.value;
        
        let url = "/api/cargas?";
        if (oUf) url += `origem_uf=${oUf}&`;
        if (dUf) url += `destino_uf=${dUf}&`;
        if (veic) url += `tipo_veiculo=${veic}&`;
        if (stat) url += `status=${stat}&`;
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            state.cargas = data;
            renderCargasList();
            updateKPIs();
        } catch (error) {
            console.error("Erro ao carregar cargas:", error);
            cargasList.innerHTML = `
                <div class="empty-list-placeholder">
                    <i class="fa-solid fa-circle-exclamation text-danger"></i>
                    <p>Erro ao conectar com a API de cargas.</p>
                </div>
            `;
        } finally {
            refreshIndicator.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Sincronizado';
        }
    }

    function renderCargasList(highlightId = null) {
        if (state.cargas.length === 0) {
            cargasList.innerHTML = `
                <div class="empty-list-placeholder">
                    <i class="fa-solid fa-folder-open"></i>
                    <p>Nenhuma carga encontrada no radar com estes filtros.</p>
                </div>
            `;
            return;
        }

        cargasList.innerHTML = "";
        state.cargas.forEach(carga => {
            const card = document.createElement("div");
            card.className = `carga-card ${carga.id_carga === state.selectedCargaId ? 'selected' : ''}`;
            if (carga.id_carga === highlightId) {
                card.classList.add("pulse-new");
            }
            
            const valorFormatado = carga.valor_frete 
                ? `R$ ${carga.valor_frete.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`
                : "A combinar";
                
            const statusClass = carga.status_agenciamento.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, '-');
            
            card.innerHTML = `
                <div class="carga-info-main">
                    <div class="route-row">
                        <span>${carga.origem_cidade}/${carga.origem_uf}</span>
                        <i class="fa-solid fa-arrow-right-long route-arrow"></i>
                        <span>${carga.destino_cidade}/${carga.destino_uf}</span>
                    </div>
                    <div class="badge-row">
                        <span class="tag-badge vehicle"><i class="fa-solid fa-truck"></i> ${carga.tipo_veiculo}</span>
                        <span class="tag-badge"><i class="fa-solid fa-truck-flatbed"></i> ${carga.tipo_carroceria}</span>
                        <span class="tag-badge product"><i class="fa-solid fa-box"></i> ${carga.produto}</span>
                        ${carga.peso_ton ? `<span class="tag-badge"><i class="fa-solid fa-weight-hanging"></i> ${carga.peso_ton}t</span>` : ''}
                    </div>
                </div>
                <div class="carga-info-side">
                    <span class="status-badge ${statusClass}">${carga.status_agenciamento}</span>
                    <span class="freight-value">${valorFormatado}</span>
                </div>
            `;
            
            card.addEventListener("click", () => {
                // Remover classe selecionada anterior
                document.querySelectorAll(".carga-card").forEach(c => c.classList.remove("selected"));
                card.classList.add("selected");
                showCargaDetails(carga.id_carga);
            });
            
            cargasList.appendChild(card);
        });
    }

    async function updateKPIs() {
        try {
            // Buscamos todas as cargas sem filtros para ter as métricas reais globais
            const response = await fetch("/api/cargas");
            const todasCargas = await response.json();
            
            const disponiveis = todasCargas.filter(c => c.status_agenciamento === "Disponível").length;
            const negociando = todasCargas.filter(c => c.status_agenciamento === "Em Negociação").length;
            const fechadas = todasCargas.filter(c => c.status_agenciamento === "Fechado").length;
            
            // Calculamos comissão simulada (R$ 150 por carga fechada)
            const comissaoTotal = fechadas * 150.00;
            
            document.getElementById("val-kpi-disponivel").innerText = disponiveis;
            document.getElementById("val-kpi-negociando").innerText = negociando;
            document.getElementById("val-kpi-fechado").innerText = fechadas;
            document.getElementById("val-kpi-comissao").innerText = `R$ ${comissaoTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        } catch (err) {
            console.error("Erro ao atualizar KPIs:", err);
        }
    }

    // ==========================================
    // DETALHES DA CARGA E MATCHMAKING
    // ==========================================
    async function showCargaDetails(cargaId) {
        state.selectedCargaId = cargaId;
        emptyDetails.classList.add("hidden");
        detailsContent.classList.remove("hidden");
        
        try {
            // Buscar carga atualizada
            const response = await fetch(`/api/cargas/${cargaId}`);
            const carga = await response.json();
            
            // Atualizar UI
            detailRoute.innerText = `${carga.origem_cidade}/${carga.origem_uf} ➔ ${carga.destino_cidade}/${carga.destino_uf}`;
            detailTime.innerText = new Date(carga.data_captura).toLocaleString('pt-BR');
            detailProduto.innerHTML = `<i class="fa-solid fa-box"></i> ${carga.produto}`;
            detailPeso.innerHTML = `<i class="fa-solid fa-weight-hanging"></i> ${carga.peso_ton ? `${carga.peso_ton} t` : 'N/A'}`;
            detailVeiculo.innerHTML = `<i class="fa-solid fa-truck"></i> ${carga.tipo_veiculo}`;
            detailCarroceria.innerHTML = `<i class="fa-solid fa-truck-flatbed"></i> ${carga.tipo_carroceria}`;
            detailContato.innerHTML = `<i class="fa-solid fa-phone"></i> ${carga.contato_origem}`;
            
            const statusClass = carga.status_agenciamento.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, '-');
            detailStatus.className = `status-badge ${statusClass}`;
            detailStatus.innerText = carga.status_agenciamento;
            
            const valorVal = carga.valor_frete 
                ? `R$ ${carga.valor_frete.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`
                : "A Combinar";
            detailValor.innerHTML = `<i class="fa-solid fa-dollar-sign"></i> ${valorVal}`;
            
            // Controla visibilidade de botões com base no status atual
            if (carga.status_agenciamento === "Fechado" || carga.status_agenciamento === "Expirado") {
                btnActionNegotiate.disabled = true;
                btnActionExpire.disabled = true;
            } else {
                btnActionNegotiate.disabled = false;
                btnActionExpire.disabled = false;
            }
            
            // Buscar Motoristas Compatíveis
            loadMatchingDrivers(cargaId);
            
        } catch (error) {
            console.error("Erro ao abrir detalhes:", error);
        }
    }

    async function loadMatchingDrivers(cargaId) {
        driversMatchList.innerHTML = `<div class="text-center p-3 text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Buscando motoristas...</div>`;
        matchCount.innerText = "0";
        
        try {
            const response = await fetch(`/api/cargas/${cargaId}/motoristas`);
            const drivers = await response.json();
            
            matchCount.innerText = drivers.length;
            
            if (drivers.length === 0) {
                driversMatchList.innerHTML = `
                    <div class="text-center p-3 text-muted" style="font-size: 12px;">
                        <i class="fa-solid fa-triangle-exclamation"></i> Nenhum motorista disponível na base para este tipo de veículo/carroceria no momento.
                    </div>
                `;
                return;
            }
            
            driversMatchList.innerHTML = "";
            drivers.forEach(driver => {
                const card = document.createElement("div");
                card.className = "driver-match-card";
                card.innerHTML = `
                    <div class="driver-info">
                        <span class="driver-name">${driver.nome}</span>
                        <span class="driver-loc"><i class="fa-solid fa-map-marker-alt"></i> Local: ${driver.cidade_atual}/${driver.uf_atual}</span>
                        <span class="driver-phone"><i class="fa-brands fa-whatsapp"></i> ${driver.telefone}</span>
                    </div>
                    <button class="btn btn-sm btn-success btn-match-trigger">
                        <i class="fa-solid fa-circle-check"></i> Disparar Match
                    </button>
                `;
                
                card.querySelector(".btn-match-trigger").addEventListener("click", () => {
                    executeMatch(cargaId, driver.id_motorista);
                });
                
                driversMatchList.appendChild(card);
            });
        } catch (error) {
            console.error("Erro ao carregar motoristas compatíveis:", error);
            driversMatchList.innerHTML = `<div class="text-danger p-2">Erro ao buscar motoristas</div>`;
        }
    }

    async function executeMatch(cargaId, motoristaId) {
        try {
            const response = await fetch("/api/match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_carga: cargaId, id_motorista: motoristaId })
            });
            const result = await response.json();
            
            if (result.success) {
                state.activeMatch = {
                    telefone: result.motorista_telefone.replace(/\D/g, ""), // limpa caracteres
                    mensagem: result.dispatch_template
                };
                
                // Abre o Modal com o template da mensagem
                matchMessageText.value = result.dispatch_template;
                matchModal.classList.remove("hidden");
                
                // Recarrega informações na tela
                loadCargas();
                showCargaDetails(cargaId);
            }
        } catch (error) {
            console.error("Erro ao realizar match:", error);
            alert("Falha ao registrar o match.");
        }
    }

    // Ações Rápidas do Detalhe
    btnActionNegotiate.addEventListener("click", async () => {
        if (!state.selectedCargaId) return;
        try {
            const response = await fetch(`/api/cargas/${state.selectedCargaId}/status`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: "Em Negociação" })
            });
            if (response.ok) {
                loadCargas();
                showCargaDetails(state.selectedCargaId);
            }
        } catch (e) {
            console.error("Erro:", e);
        }
    });

    btnActionExpire.addEventListener("click", async () => {
        if (!state.selectedCargaId) return;
        try {
            const response = await fetch(`/api/cargas/${state.selectedCargaId}/status`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: "Expirado" })
            });
            if (response.ok) {
                loadCargas();
                showCargaDetails(state.selectedCargaId);
            }
        } catch (e) {
            console.error("Erro:", e);
        }
    });

    // ==========================================
    // ROBÔ DE CAPTAÇÃO / SIMULADOR
    // ==========================================
    function logTerminal(message, type = "info") {
        const time = new Date().toLocaleTimeString('pt-BR');
        const line = document.createElement("div");
        line.className = `log-line ${type}`;
        line.innerHTML = `<span class="text-muted">[${time}]</span> ${message}`;
        terminalLogBody.appendChild(line);
        terminalLogBody.scrollTop = terminalLogBody.scrollHeight;
    }

    scrapeTriggerBtn.addEventListener("click", async () => {
        scrapeTriggerBtn.disabled = true;
        const icon = scrapeTriggerBtn.querySelector("i");
        icon.className = "fa-solid fa-arrows-rotate fa-spin";
        
        logTerminal("Iniciando varredura manual de painéis públicos e WhatsApp...", "info");
        
        try {
            const response = await fetch("/api/scraper/trigger", { method: "POST" });
            const result = await response.json();
            
            setTimeout(() => {
                logTerminal(`Conectando ao canal de mensagens: ${result.parsed_data.contato_origem}`, "info");
            }, 500);
            
            setTimeout(() => {
                logTerminal(`Mensagem captada: "${result.raw_message.substring(0, 70)}..."`, "warn");
            }, 1000);
            
            setTimeout(() => {
                logTerminal(`Estruturando dados: ${result.parsed_data.origem_cidade}/${result.parsed_data.origem_uf} -> ${result.parsed_data.destino_cidade}/${result.parsed_data.destino_uf} | Veículo: ${result.parsed_data.tipo_veiculo}`, "info");
            }, 1500);

            setTimeout(() => {
                if (result.is_new) {
                    logTerminal(`✓ Sucesso! Nova Carga inserida no SQLite (ID: ${result.carga_id})`, "success");
                    loadCargas().then(() => {
                        renderCargasList(result.carga_id);
                        showCargaDetails(result.carga_id);
                    });
                } else {
                    logTerminal(`⚠️ Carga ignorada! Identificada duplicidade recente no banco de dados (ID existente: ${result.carga_id})`, "warn");
                    alert("Varredura concluída: Carga descartada por ser duplicada de uma postagem recente.");
                }
                
                scrapeTriggerBtn.disabled = false;
                icon.className = "fa-solid fa-magnifying-glass animate-spin-hover";
            }, 2000);
            
        } catch (error) {
            console.error("Erro na simulação:", error);
            logTerminal("✖ Falha crítica no motor de navegação.", "warn");
            scrapeTriggerBtn.disabled = false;
            icon.className = "fa-solid fa-magnifying-glass animate-spin-hover";
        }
    });

    // ==========================================
    // CAIXA DE AREIA REGEX (SANDBOX PARSER)
    // ==========================================
    btnParseSubmit.addEventListener("click", async () => {
        const text = rawTextInput.value.trim();
        if (!text) {
            alert("Por favor, cole um texto primeiro!");
            return;
        }
        
        btnParseSubmit.disabled = true;
        btnParseSubmit.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processando Regex...';
        
        try {
            const response = await fetch("/api/scraper/parse-text", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });
            const result = await response.json();
            
            // Renderizar resultado visual
            parserResultCard.classList.remove("hidden");
            const data = result.parsed_data;
            
            const valorFormat = data.valor_frete 
                ? `R$ ${data.valor_frete.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`
                : "A combinar";
                
            parsedOutputGrid.innerHTML = `
                <div class="detail-item">
                    <span class="lbl">Origem</span>
                    <span class="val"><i class="fa-solid fa-location-dot"></i> ${data.origem_cidade}/${data.origem_uf}</span>
                </div>
                <div class="detail-item">
                    <span class="lbl">Destino</span>
                    <span class="val"><i class="fa-solid fa-map-pin"></i> ${data.destino_cidade}/${data.destino_uf}</span>
                </div>
                <div class="detail-item">
                    <span class="lbl">Veículo</span>
                    <span class="val"><i class="fa-solid fa-truck"></i> ${data.tipo_veiculo}</span>
                </div>
                <div class="detail-item">
                    <span class="lbl">Carroceria</span>
                    <span class="val"><i class="fa-solid fa-truck-flatbed"></i> ${data.tipo_carroceria}</span>
                </div>
                <div class="detail-item">
                    <span class="lbl">Produto</span>
                    <span class="val"><i class="fa-solid fa-box"></i> ${data.produto}</span>
                </div>
                <div class="detail-item">
                    <span class="lbl">Peso</span>
                    <span class="val"><i class="fa-solid fa-weight-hanging"></i> ${data.peso_ton ? `${data.peso_ton} t` : 'Não identificado'}</span>
                </div>
                <div class="detail-item">
                    <span class="lbl">Valor Extraído</span>
                    <span class="val price"><i class="fa-solid fa-dollar-sign"></i> ${valorFormat}</span>
                </div>
                <div class="detail-item">
                    <span class="lbl">Contato do Embarcador</span>
                    <span class="val contato"><i class="fa-solid fa-phone"></i> ${data.contato_origem}</span>
                </div>
            `;
            
            const alertBox = document.getElementById("parser-db-alert");
            if (result.is_new) {
                alertBox.className = "parser-alert success";
                alertBox.innerHTML = `<i class="fa-solid fa-circle-check"></i> Sucesso! Dados estruturados e salvos no SQLite como uma nova oportunidade.`;
            } else {
                alertBox.className = "parser-alert warn";
                alertBox.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Duplicidade detectada! O registro recente já existia no banco (ID existente: ${result.carga_id}).`;
            }
            
            // Limpa textarea e reseta botão
            rawTextInput.value = "";
            updateKPIs();
            
        } catch (error) {
            console.error("Erro:", error);
            alert("Ocorreu um erro no parsing da mensagem.");
        } finally {
            btnParseSubmit.disabled = false;
            btnParseSubmit.innerHTML = '<i class="fa-solid fa-gears"></i> Processar e Cadastrar Carga';
        }
    });

    // ==========================================
    // OPERAÇÕES DO MODAL
    // ==========================================
    function closeModal() {
        matchModal.classList.add("hidden");
        state.activeMatch = null;
    }

    btnCloseModal.addEventListener("click", closeModal);
    btnModalCancel.addEventListener("click", closeModal);
    
    // Copiar Mensagem
    btnCopyMsg.addEventListener("click", () => {
        matchMessageText.select();
        navigator.clipboard.writeText(matchMessageText.value);
        btnCopyMsg.innerHTML = '<i class="fa-solid fa-clipboard-check"></i> Copiado!';
        setTimeout(() => {
            btnCopyMsg.innerHTML = '<i class="fa-regular fa-copy"></i> Copiar Texto';
        }, 2000);
    });

    // Enviar WhatsApp Web
    btnModalSendWhatsapp.addEventListener("click", () => {
        if (!state.activeMatch) return;
        const phone = state.activeMatch.telefone;
        const msg = encodeURIComponent(state.activeMatch.mensagem);
        const url = `https://web.whatsapp.com/send?phone=55${phone}&text=${msg}`;
        window.open(url, "_blank");
    });

    // ==========================================
    // EVENT LISTENER DE FILTROS
    // ==========================================
    [filterOrigemUf, filterDestinoUf, filterVeiculo, filterStatus].forEach(filter => {
        filter.addEventListener("change", loadCargas);
    });

    // Inicialização da Tela
    loadCargas();
});
