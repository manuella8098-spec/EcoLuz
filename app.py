import math
from io import BytesIO
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

HORAS_ANO = 4380
RELACAO_MAXIMA = 3.5

st.set_page_config(
    page_title="EcoLuz | Iluminação Pública",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Cálculos ----------
def numero_postes(comprimento_m, espacamento_m):
    return int(comprimento_m // espacamento_m) + 1

def consumo_anual(n_luminarias, potencia_w):
    return n_luminarias * potencia_w * HORAS_ANO / 1000

def demanda_kw(n_luminarias, potencia_w):
    return n_luminarias * potencia_w / 1000

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def numero_br(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_resultados(ruas, cfg):
    total = sum(r["postes"] for r in ruas)
    atual_kwh = consumo_anual(total, cfg["potencia_atual"])
    led_kwh = consumo_anual(total, cfg["potencia_led"])
    reducao_kwh = atual_kwh - led_kwh
    reducao_pct = (reducao_kwh / atual_kwh * 100) if atual_kwh else 0
    economia_energia = reducao_kwh * cfg["tarifa"]
    manutencao = total * HORAS_ANO / cfg["vida_convencional"] * cfg["custo_troca"]
    investimento = total * cfg["custo_led"]
    economia_anual = economia_energia + manutencao
    payback = investimento / economia_anual if economia_anual > 0 else None
    horizonte = max(1, int(cfg["vida_led"] // HORAS_ANO))
    tarifa = cfg["tarifa"]
    acumulado = 0
    ano_retorno = None
    projecao = []
    for ano in range(1, horizonte + 1):
        econ_energia_ano = reducao_kwh * tarifa
        econ_total_ano = econ_energia_ano + manutencao
        acumulado += econ_total_ano
        projecao.append({
            "Ano": ano,
            "Tarifa (R$/kWh)": tarifa,
            "Economia de energia (R$)": econ_energia_ano,
            "Manutenção evitada (R$)": manutencao,
            "Economia anual total (R$)": econ_total_ano,
            "Economia acumulada (R$)": acumulado,
            "Saldo após investimento (R$)": acumulado - investimento,
        })
        if ano_retorno is None and acumulado >= investimento:
            ano_retorno = ano
        tarifa *= (1 + cfg["reajuste"] / 100)
    relatorio_ruas = []
    for rua in ruas:
        relacao = rua["espacamento"] / rua["altura"]
        max_esp = RELACAO_MAXIMA * rua["altura"]
        sugeridos = numero_postes(rua["comprimento"], max_esp) if relacao > RELACAO_MAXIMA else rua["postes"]
        relatorio_ruas.append({
            "Rua": rua["nome"],
            "Comprimento (m)": rua["comprimento"],
            "Altura do poste (m)": rua["altura"],
            "Espaçamento (m)": rua["espacamento"],
            "Postes estimados": rua["postes"],
            "Relação espaçamento/altura": relacao,
            "Situação": "Adequado pela regra simplificada" if relacao <= RELACAO_MAXIMA else "Revisar espaçamento",
            "Espaçamento máximo sugerido (m)": max_esp,
            "Postes sugeridos": sugeridos,
            "Postes adicionais": max(0, sugeridos - rua["postes"]),
        })
    return {
        "total": total, "atual_kwh": atual_kwh, "led_kwh": led_kwh,
        "reducao_kwh": reducao_kwh, "reducao_pct": reducao_pct,
        "demanda_atual": demanda_kw(total, cfg["potencia_atual"]),
        "demanda_led": demanda_kw(total, cfg["potencia_led"]),
        "economia_energia": economia_energia, "manutencao": manutencao,
        "investimento": investimento, "economia_anual": economia_anual,
        "payback": payback, "horizonte": horizonte, "ano_retorno": ano_retorno,
        "projecao": pd.DataFrame(projecao),
        "ruas_df": pd.DataFrame(relatorio_ruas),
        "saldo_final": acumulado - investimento,
        "economia_acumulada": acumulado,
    }

def classificar_payback(anos):
    if anos is None:
        return "Não calculável"
    if anos <= 4:
        return "Excelente"
    if anos <= 7:
        return "Bom"
    if anos <= 10:
        return "Regular"
    return "Pouco atrativo"

def gerar_relatorio_md(ruas, cfg, r):
    linhas = [
        "# EcoLuz — Relatório de análise de iluminação pública",
        f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "## 1. Objetivo",
        "Comparar o cenário de iluminação atual com uma alternativa LED, estimando consumo, redução de energia, custos, manutenção e retorno financeiro.",
        "",
        "## 2. Dados adotados",
        f"- Ruas analisadas: {len(ruas)}",
        f"- Postes/luminárias estimados: {r['total']}",
        f"- Potência convencional: {numero_br(cfg['potencia_atual'])} W",
        f"- Potência LED proposta: {numero_br(cfg['potencia_led'])} W",
        f"- Tarifa de energia: {moeda(cfg['tarifa'])}/kWh",
        f"- Custo de luminária LED instalada: {moeda(cfg['custo_led'])}",
        f"- Vida útil convencional: {numero_br(cfg['vida_convencional'], 0)} h",
        f"- Vida útil LED: {numero_br(cfg['vida_led'], 0)} h",
        f"- Custo por troca convencional: {moeda(cfg['custo_troca'])}",
        f"- Reajuste anual da tarifa considerado: {numero_br(cfg['reajuste'])}%",
        "",
        "## 3. Levantamento das ruas",
        r["ruas_df"].to_markdown(index=False),
        "",
        "## 4. Comparação energética",
        f"- Consumo atual estimado: {numero_br(r['atual_kwh'])} kWh/ano",
        f"- Consumo com LED estimado: {numero_br(r['led_kwh'])} kWh/ano",
        f"- Redução estimada: {numero_br(r['reducao_kwh'])} kWh/ano ({numero_br(r['reducao_pct'], 1)}%)",
        f"- Demanda nominal atual: {numero_br(r['demanda_atual'])} kW",
        f"- Demanda nominal com LED: {numero_br(r['demanda_led'])} kW",
        "",
        "## 5. Viabilidade econômica",
        f"- Economia de energia no primeiro ano: {moeda(r['economia_energia'])}",
        f"- Manutenção evitada estimada por ano: {moeda(r['manutencao'])}",
        f"- Economia anual total inicial: {moeda(r['economia_anual'])}",
        f"- Investimento estimado: {moeda(r['investimento'])}",
        f"- Payback simples: {numero_br(r['payback'])} anos — {classificar_payback(r['payback'])}" if r["payback"] is not None else "- Payback simples: não calculável, pois a economia anual não é positiva.",
        f"- Horizonte de projeção: {r['horizonte']} anos",
        f"- Ano de retorno na projeção: {r['ano_retorno'] if r['ano_retorno'] is not None else 'não alcançado no horizonte'}",
        f"- Economia acumulada projetada: {moeda(r['economia_acumulada'])}",
        f"- Saldo após descontar o investimento: {moeda(r['saldo_final'])}",
        "",
        "## 6. Recomendação preliminar",
    ]
    if r["payback"] is not None and r["reducao_pct"] > 0 and r["payback"] <= 7:
        linhas.append("A substituição pode ser economicamente interessante no cenário informado. Recomenda-se confirmar preços, tarifa, equivalência luminotécnica e condições reais de instalação antes da decisão.")
    else:
        linhas.append("Recomenda-se revisar os custos, potências, tarifa e condições de instalação antes de decidir pela substituição.")
    linhas += [
        "",
        "## 7. Limitações",
        "O cálculo de espaçamento é uma verificação simplificada baseada na relação espaçamento/altura indicada no projeto acadêmico. Não substitui estudo luminotécnico, vistoria em campo, projeto executivo, avaliação de uniformidade, ofuscamento, segurança elétrica ou normas aplicáveis.",
        "",
        "## 8. Metodologia",
        f"Foi considerado o regime de {HORAS_ANO:,} horas anuais. O consumo anual foi estimado por quantidade de luminárias × potência em watts × horas anuais ÷ 1.000. A projeção considera o reajuste anual informado e mantém a estimativa de manutenção evitada constante.",
        "",
        "**Projeto acadêmico — Bases de Programação. Os resultados são estimativas e dependem da qualidade dos dados inseridos.**",
    ]
    return "\n".join(linhas)

# ---------- Estado da aplicação ----------
if "ruas" not in st.session_state:
    st.session_state.ruas = []
if "config" not in st.session_state:
    st.session_state.config = {
        "potencia_atual": 150.0, "potencia_led": 70.0, "tarifa": 0.60,
        "custo_led": 900.0, "vida_convencional": 24000.0,
        "custo_troca": 250.0, "vida_led": 50000.0, "reajuste": 5.0,
    }

# ---------- Aparência ----------
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px;}
.ecoluz-subtitle {color: #6b7280; font-size: 1rem;}
div[data-testid="stMetric"] {background: rgba(90, 120, 100, 0.08); padding: 14px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# 💡 EcoLuz")
    st.caption("Gestão inteligente da iluminação pública")
    pagina = st.radio("Navegação", ["Visão geral", "Cadastro de ruas", "Parâmetros", "Análise energética", "Viabilidade econômica", "Relatório final"])
    st.divider()
    st.caption("Projeto 3 • Bases de Programação • ODS 11")
    st.caption("Valores estimados para fins acadêmicos.")

st.title("💡 EcoLuz")
st.markdown('<p class="ecoluz-subtitle">Análise de eficiência energética e viabilidade econômica da iluminação pública</p>', unsafe_allow_html=True)

# Avenidas/ruas de demonstração
amostra = [
    {"nome": "Rua das Acácias", "comprimento": 400.0, "altura": 9.0, "espacamento": 30.0, "postes": numero_postes(400, 30)},
    {"nome": "Rua do Mercado", "comprimento": 250.0, "altura": 8.0, "espacamento": 35.0, "postes": numero_postes(250, 35)},
    {"nome": "Avenida Central", "comprimento": 600.0, "altura": 10.0, "espacamento": 35.0, "postes": numero_postes(600, 35)},
]

if pagina == "Visão geral":
    st.subheader("Painel de controle")
    st.write("Cadastre ruas e ajuste os parâmetros para gerar a comparação de consumo, a análise econômica e o relatório.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Ruas cadastradas", len(st.session_state.ruas))
    col2.metric("Postes estimados", sum(x["postes"] for x in st.session_state.ruas))
    col3.metric("Horas consideradas/ano", f"{HORAS_ANO:,}".replace(",", "."))
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### Começar rapidamente")
        if st.button("Carregar dados de demonstração", type="primary", use_container_width=True):
            st.session_state.ruas = [x.copy() for x in amostra]
            st.success("Dados de demonstração carregados.")
            st.rerun()
        if st.button("Limpar todas as ruas", use_container_width=True):
            st.session_state.ruas = []
            st.rerun()
    with c2:
        st.markdown("#### Parâmetros atuais")
        cfg = st.session_state.config
        st.write(f"**Convencional:** {numero_br(cfg['potencia_atual'])} W")
        st.write(f"**LED:** {numero_br(cfg['potencia_led'])} W")
        st.write(f"**Tarifa:** {moeda(cfg['tarifa'])}/kWh")
        st.write(f"**Custo LED instalado:** {moeda(cfg['custo_led'])}")
    if st.session_state.ruas:
        df = pd.DataFrame(st.session_state.ruas)
        st.markdown("#### Ruas cadastradas")
        st.dataframe(df.rename(columns={"nome":"Rua", "comprimento":"Comprimento (m)", "altura":"Altura do poste (m)", "espacamento":"Espaçamento (m)", "postes":"Postes estimados"}), use_container_width=True, hide_index=True)
    st.info("Os dados de demonstração são fictícios e servem apenas para testar o funcionamento. Substitua-os por dados levantados em campo.")

elif pagina == "Cadastro de ruas":
    st.subheader("Cadastro de ruas e avenidas")
    with st.form("form_rua", clear_on_submit=True):
        nome = st.text_input("Nome da rua ou avenida")
        c1, c2, c3 = st.columns(3)
        comprimento = c1.number_input("Comprimento (m)", min_value=1.0, value=400.0, step=10.0)
        altura = c2.number_input("Altura dos postes (m)", min_value=1.0, value=9.0, step=0.5)
        espacamento = c3.number_input("Espaçamento entre postes (m)", min_value=1.0, value=30.0, step=1.0)
        enviado = st.form_submit_button("Adicionar rua", type="primary")
    if enviado:
        if not nome.strip():
            st.error("Informe o nome da rua.")
        elif any(x["nome"].casefold() == nome.strip().casefold() for x in st.session_state.ruas):
            st.error("Já existe uma rua com esse nome. Use um nome diferente.")
        else:
            st.session_state.ruas.append({
                "nome": nome.strip(), "comprimento": float(comprimento),
                "altura": float(altura), "espacamento": float(espacamento),
                "postes": numero_postes(comprimento, espacamento),
            })
            st.success(f"Rua adicionada: {numero_postes(comprimento, espacamento)} postes estimados.")
            st.rerun()
    st.markdown("#### Ruas cadastradas")
    if st.session_state.ruas:
        if st.button("Remover todas as ruas", type="secondary"):
            st.session_state.ruas = []
            st.rerun()
        df = pd.DataFrame(st.session_state.ruas)
        st.dataframe(df.rename(columns={"nome":"Rua", "comprimento":"Comprimento (m)", "altura":"Altura do poste (m)", "espacamento":"Espaçamento (m)", "postes":"Postes estimados"}), use_container_width=True, hide_index=True)
        opcoes = [x["nome"] for x in st.session_state.ruas]
        remover = st.selectbox("Selecionar rua para remover", ["— Selecione —"] + opcoes)
        if st.button("Remover rua selecionada") and remover != "— Selecione —":
            st.session_state.ruas = [x for x in st.session_state.ruas if x["nome"] != remover]
            st.rerun()
    else:
        st.info("Ainda não há ruas cadastradas. Adicione uma acima ou carregue os dados de demonstração na Visão geral.")

elif pagina == "Parâmetros":
    st.subheader("Luminárias, tarifas e custos")
    cfg = st.session_state.config
    with st.form("form_config"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Iluminação")
            tipo = st.selectbox("Tecnologia atual", ["Vapor de sódio", "Vapor de mercúrio", "Outra"], index=0)
            potencia_atual = st.number_input("Potência atual por luminária (W)", min_value=1.0, value=float(cfg["potencia_atual"]), step=10.0)
            potencia_led = st.number_input("Potência LED proposta (W)", min_value=1.0, value=float(cfg["potencia_led"]), step=5.0)
            vida_convencional = st.number_input("Vida útil convencional (horas)", min_value=1.0, value=float(cfg["vida_convencional"]), step=1000.0)
            vida_led = st.number_input("Vida útil LED (horas)", min_value=1.0, value=float(cfg["vida_led"]), step=1000.0)
        with c2:
            st.markdown("#### Custos e energia")
            tarifa = st.number_input("Tarifa de energia (R$/kWh)", min_value=0.0, value=float(cfg["tarifa"]), step=0.05, format="%.3f")
            custo_led = st.number_input("Custo por luminária LED instalada (R$)", min_value=0.0, value=float(cfg["custo_led"]), step=50.0)
            custo_troca = st.number_input("Custo por troca convencional (R$)", min_value=0.0, value=float(cfg["custo_troca"]), step=10.0)
            reajuste = st.number_input("Reajuste anual da tarifa (%)", min_value=0.0, max_value=100.0, value=float(cfg["reajuste"]), step=0.5)
        salvar = st.form_submit_button("Salvar parâmetros", type="primary")
    if salvar:
        if potencia_led >= potencia_atual:
            st.warning("A potência LED informada não é menor que a atual. Confira se as luminárias são equivalentes em desempenho luminoso.")
        st.session_state.config = {
            "potencia_atual": potencia_atual, "potencia_led": potencia_led,
            "tarifa": tarifa, "custo_led": custo_led,
            "vida_convencional": vida_convencional, "custo_troca": custo_troca,
            "vida_led": vida_led, "reajuste": reajuste,
        }
        st.success("Parâmetros salvos.")
        st.rerun()
    st.caption("A potência, isoladamente, não comprova equivalência luminotécnica. Compare também fluxo luminoso, distribuição fotométrica e condições da via.")

elif pagina in ["Análise energética", "Viabilidade econômica", "Relatório final"]:
    if not st.session_state.ruas:
        st.warning("Cadastre pelo menos uma rua ou carregue os dados de demonstração na Visão geral.")
        st.stop()
    cfg = st.session_state.config
    r = calcular_resultados(st.session_state.ruas, cfg)
    if pagina == "Análise energética":
        st.subheader("Comparação de consumo e demanda")
        a, b, c = st.columns(3)
        a.metric("Consumo atual", f"{numero_br(r['atual_kwh'], 0)} kWh/ano")
        b.metric("Consumo com LED", f"{numero_br(r['led_kwh'], 0)} kWh/ano")
        c.metric("Redução estimada", f"{numero_br(r['reducao_pct'], 1)}%", f"{numero_br(r['reducao_kwh'], 0)} kWh/ano")
        df_consumo = pd.DataFrame({
            "Cenário": ["Atual", "Com LED"],
            "Consumo anual (kWh)": [r["atual_kwh"], r["led_kwh"]],
            "Demanda nominal (kW)": [r["demanda_atual"], r["demanda_led"]],
        })
        fig = px.bar(df_consumo, x="Cenário", y="Consumo anual (kWh)", color="Cenário", title="Consumo anual estimado")
        st.plotly_chart(fig, use_container_width=True)
        fig2 = px.bar(df_consumo, x="Cenário", y="Demanda nominal (kW)", color="Cenário", title="Demanda nominal estimada")
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df_consumo, use_container_width=True, hide_index=True)
        st.markdown("#### Verificação de espaçamento")
        st.dataframe(r["ruas_df"], use_container_width=True, hide_index=True)
        st.download_button("Baixar levantamento das ruas (CSV)", r["ruas_df"].to_csv(index=False).encode("utf-8-sig"), "levantamento_ecoluz.csv", "text/csv")
    elif pagina == "Viabilidade econômica":
        st.subheader("Viabilidade econômica")
        a, b, c, d = st.columns(4)
        a.metric("Investimento estimado", moeda(r["investimento"]))
        b.metric("Economia anual inicial", moeda(r["economia_anual"]))
        c.metric("Payback simples", f"{numero_br(r['payback'], 1)} anos" if r["payback"] is not None else "Não calculável")
        d.metric("Classificação", classificar_payback(r["payback"]))
        c1, c2 = st.columns(2)
        c1.metric("Economia de energia no 1º ano", moeda(r["economia_energia"]))
        c2.metric("Manutenção evitada estimada/ano", moeda(r["manutencao"]))
        if r["payback"] is not None and r["payback"] <= 4:
            st.success("Pela classificação simplificada do projeto, o retorno é excelente.")
        elif r["payback"] is not None and r["payback"] <= 7:
            st.success("Pela classificação simplificada do projeto, o retorno é bom.")
        elif r["payback"] is not None and r["payback"] <= 10:
            st.warning("Pela classificação simplificada do projeto, o retorno é regular.")
        else:
            st.warning("O retorno pode ser pouco atrativo. Revise as premissas e os custos.")
        proj = r["projecao"]
        fig = px.line(proj, x="Ano", y=["Economia acumulada (R$)"], markers=True, title="Economia acumulada projetada")
        fig.add_hline(y=r["investimento"], line_dash="dash", annotation_text="Investimento inicial")
        st.plotly_chart(fig, use_container_width=True)
        fig2 = px.bar(proj, x="Ano", y="Economia anual total (R$)", title="Economia anual projetada")
        st.plotly_chart(fig2, use_container_width=True)
        e1, e2, e3 = st.columns(3)
        e1.metric("Horizonte de projeção", f"{r['horizonte']} anos")
        e2.metric("Ano de retorno", str(r["ano_retorno"]) if r["ano_retorno"] is not None else "Não alcançado")
        e3.metric("Saldo após investimento", moeda(r["saldo_final"]))
        st.dataframe(proj.style.format({
            "Tarifa (R$/kWh)": "R$ {:.3f}",
            "Economia de energia (R$)": "R$ {:,.2f}",
            "Manutenção evitada (R$)": "R$ {:,.2f}",
            "Economia anual total (R$)": "R$ {:,.2f}",
            "Economia acumulada (R$)": "R$ {:,.2f}",
            "Saldo após investimento (R$)": "R$ {:,.2f}",
        }), use_container_width=True, hide_index=True)
        st.download_button("Baixar projeção financeira (CSV)", proj.to_csv(index=False).encode("utf-8-sig"), "projecao_financeira_ecoluz.csv", "text/csv")
    else:
        st.subheader("Relatório final")
        if r["payback"] is not None and r["reducao_pct"] > 0 and r["payback"] <= 7:
            recomendacao = "A substituição pode ser economicamente interessante no cenário informado."
        else:
            recomendacao = "Recomenda-se revisar os dados e os custos antes de decidir pela substituição."
        st.markdown(f"### Recomendação preliminar\n{recomendacao}")
        st.caption("Esta recomendação é baseada apenas nos dados inseridos e não substitui estudo luminotécnico ou análise técnica em campo.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Ruas", len(st.session_state.ruas))
        m2.metric("Postes/luminárias", r["total"])
        m3.metric("Redução de consumo", f"{numero_br(r['reducao_pct'], 1)}%")
        st.markdown("#### Resumo energético e financeiro")
        resumo = pd.DataFrame([
            {"Indicador": "Consumo atual", "Resultado": f"{numero_br(r['atual_kwh'])} kWh/ano"},
            {"Indicador": "Consumo com LED", "Resultado": f"{numero_br(r['led_kwh'])} kWh/ano"},
            {"Indicador": "Redução de energia", "Resultado": f"{numero_br(r['reducao_kwh'])} kWh/ano"},
            {"Indicador": "Economia anual inicial", "Resultado": moeda(r["economia_anual"])},
            {"Indicador": "Investimento estimado", "Resultado": moeda(r["investimento"])},
            {"Indicador": "Payback simples", "Resultado": f"{numero_br(r['payback'])} anos" if r["payback"] is not None else "Não calculável"},
            {"Indicador": "Saldo projetado", "Resultado": moeda(r["saldo_final"])},
        ])
        st.dataframe(resumo, use_container_width=True, hide_index=True)
        st.markdown("#### Levantamento das ruas")
        st.dataframe(r["ruas_df"], use_container_width=True, hide_index=True)
        relatorio = gerar_relatorio_md(st.session_state.ruas, cfg, r)
        st.download_button("📄 Baixar relatório final (Markdown)", relatorio.encode("utf-8"), "relatorio_final_ecoluz.md", "text/markdown", type="primary")
        st.download_button("📊 Baixar dados das ruas (CSV)", r["ruas_df"].to_csv(index=False).encode("utf-8-sig"), "ruas_ecoluz.csv", "text/csv")
        st.download_button("📈 Baixar projeção financeira (CSV)", r["projecao"].to_csv(index=False).encode("utf-8-sig"), "projecao_ecoluz.csv", "text/csv")

st.divider()
st.caption("EcoLuz • Protótipo acadêmico • Cálculos estimativos • Verifique os dados de entrada antes de usar os resultados.")
