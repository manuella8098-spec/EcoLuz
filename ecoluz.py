# EcoLuz — Projeto 3: Iluminação Pública Eficiente
# Bases de Programação — UniJorge
# Versão inicial: cadastro de ruas, espaçamento, consumo e viabilidade econômica.

HORAS_ANO = 12 * 365
RELACAO_MAXIMA = 3.5

def numero_postes(comprimento_m, espacamento_m):
    """Calcula o número estimado de postes conforme a regra do projeto."""
    return int(comprimento_m // espacamento_m) + 1

def relacao_espacamento(espacamento_m, altura_m):
    """Retorna a relação entre espaçamento e altura do poste."""
    return espacamento_m / altura_m

def espacamento_adequado(relacao):
    """Verifica se a relação atende ao limite simplificado de 3,5."""
    return relacao <= RELACAO_MAXIMA

def consumo_anual(n_luminarias, potencia_w):
    """Consumo anual em kWh, considerando 4.380 horas por ano."""
    return n_luminarias * potencia_w * HORAS_ANO / 1000

def demanda_kw(n_luminarias, potencia_w):
    """Demanda nominal total em kW."""
    return n_luminarias * potencia_w / 1000

def manutencao_evitada(n, vida_util_h, custo_troca):
    """Estimativa anual de manutenção evitada, conforme o enunciado."""
    return n * HORAS_ANO / vida_util_h * custo_troca

def payback_simples(investimento, economia_anual):
    """Retorna o payback em anos; None quando não há economia positiva."""
    if economia_anual <= 0:
        return None
    return investimento / economia_anual

def classificar_payback(anos):
    if anos is None:
        return "Não calculável"
    if anos <= 4:
        return "Excelente"
    elif anos <= 7:
        return "Bom"
    elif anos <= 10:
        return "Regular"
    return "Pouco atrativo"

def ler_float(mensagem, minimo=None):
    """Lê número aceitando vírgula decimal e repete até receber valor válido."""
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))
            if minimo is not None and valor <= minimo:
                print(f"Digite um valor maior que {minimo}.")
                continue
            return valor
        except ValueError:
            print("Valor inválido. Tente novamente usando números, por exemplo 12,5.")

def ler_inteiro(mensagem, minimo=None):
    while True:
        try:
            valor = int(input(mensagem))
            if minimo is not None and valor < minimo:
                print(f"Digite um número igual ou maior que {minimo}.")
                continue
            return valor
        except ValueError:
            print("Digite um número inteiro válido.")

def cadastrar_ruas(ruas):
    print("\n=== CADASTRO DE RUAS ===")
    print("Digite 'fim' como nome para encerrar o cadastro.")
    while True:
        nome = input("\nNome da rua: ").strip()
        if nome.lower() == "fim":
            break
        if not nome:
            print("O nome não pode ficar vazio.")
            continue
        comprimento = ler_float("Comprimento da rua (m): ", 0)
        altura = ler_float("Altura dos postes (m): ", 0)
        espacamento = ler_float("Espaçamento entre postes (m): ", 0)
        n_postes = numero_postes(comprimento, espacamento)
        ruas.append({
            "nome": nome,
            "comprimento": comprimento,
            "altura": altura,
            "espacamento": espacamento,
            "postes": n_postes
        })
        print(f"Rua cadastrada: {nome} — {n_postes} postes estimados.")
    if ruas:
        print(f"\nCadastro concluído. Ruas cadastradas: {len(ruas)}.")
    else:
        print("Nenhuma rua cadastrada.")

def listar_ruas(ruas):
    if not ruas:
        print("\nCadastre pelo menos uma rua primeiro.")
        return
    print("\n=== LEVANTAMENTO DAS RUAS ===")
    total_postes = 0
    for rua in ruas:
        relacao = relacao_espacamento(rua["espacamento"], rua["altura"])
        total_postes += rua["postes"]
        print(f"\nRua: {rua['nome']}")
        print(f"  Comprimento: {rua['comprimento']:.1f} m")
        print(f"  Altura dos postes: {rua['altura']:.1f} m")
        print(f"  Espaçamento: {rua['espacamento']:.1f} m")
        print(f"  Postes estimados: {rua['postes']}")
        print(f"  Relação espaçamento/altura: {relacao:.2f}")
        if espacamento_adequado(relacao):
            print("  Situação: espaçamento adequado pela regra simplificada.")
        else:
            espacamento_maximo = RELACAO_MAXIMA * rua["altura"]
            postes_sugeridos = numero_postes(rua["comprimento"], espacamento_maximo)
            adicionais = max(0, postes_sugeridos - rua["postes"])
            print("  ALERTA: espaçamento excessivo — podem existir trechos escuros.")
            print(f"  Espaçamento máximo sugerido: {espacamento_maximo:.2f} m")
            print(f"  Postes sugeridos: {postes_sugeridos} ({adicionais} a mais)")
    print(f"\nTOTAL ESTIMADO DE POSTES/LUMINÁRIAS: {total_postes}")

def escolher_potencia_atual():
    print("\nTipo de luminária atual:")
    print("1 - Vapor de sódio 70 W")
    print("2 - Vapor de sódio 150 W")
    print("3 - Vapor de sódio 250 W")
    print("4 - Vapor de mercúrio 250 W")
    print("5 - Outra potência")
    while True:
        opcao = input("Escolha uma opção (1 a 5): ").strip()
        potencias = {"1": 70, "2": 150, "3": 250, "4": 250}
        if opcao in potencias:
            return potencias[opcao]
        if opcao == "5":
            return ler_float("Digite a potência atual em W: ", 0)
        print("Opção inválida.")

def configurar_luminarias(config):
    print("\n=== CONFIGURAÇÃO DAS LUMINÁRIAS ===")
    config["potencia_atual"] = escolher_potencia_atual()
    while True:
        led = ler_float("Potência da luminária LED proposta (W): ", 0)
        if led >= config["potencia_atual"]:
            print("Atenção: para a comparação deste projeto, informe uma potência LED menor que a atual.")
            continuar = input("Deseja informar outra potência? (s/n): ").strip().lower()
            if continuar == "s":
                continue
            print("Potência registrada mesmo assim; confira se a luminária LED é equivalente em iluminação.")
        config["potencia_led"] = led
        break
    config["tarifa"] = ler_float("Tarifa de energia (R$/kWh): ", 0)
    config["custo_led"] = ler_float("Custo por luminária LED instalada (R$): ", 0)
    config["vida_convencional"] = ler_float("Vida útil da lâmpada convencional (h): ", 0)
    config["custo_troca"] = ler_float("Custo de cada troca convencional (R$): ", 0)
    config["vida_led"] = ler_float("Vida útil da luminária LED (h): ", 0)
    config["reajuste"] = ler_float("Reajuste anual da tarifa (%): ", -0.000001)
    config["configurada"] = True
    print("Dados das luminárias e custos registrados.")

def obter_total_luminarias(ruas):
    return sum(rua["postes"] for rua in ruas)

def comparar_consumo(ruas, config):
    if not ruas:
        print("\nCadastre pelo menos uma rua primeiro.")
        return
    if not config["configurada"]:
        print("\nConfigure as luminárias primeiro (opção 3).")
        return
    n = obter_total_luminarias(ruas)
    atual = consumo_anual(n, config["potencia_atual"])
    led = consumo_anual(n, config["potencia_led"])
    reducao = atual - led
    percentual = (reducao / atual * 100) if atual else 0
    print("\n=== COMPARAÇÃO DO CONSUMO ===")
    print(f"Total de luminárias: {n}")
    print(f"Consumo atual: {atual:,.2f} kWh/ano".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Consumo com LED: {led:,.2f} kWh/ano".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Redução: {reducao:,.2f} kWh/ano ({percentual:.1f}%)".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Demanda atual: {demanda_kw(n, config['potencia_atual']):.2f} kW")
    print(f"Demanda com LED: {demanda_kw(n, config['potencia_led']):.2f} kW")

def analisar_viabilidade(ruas, config):
    if not ruas:
        print("\nCadastre pelo menos uma rua primeiro.")
        return
    if not config["configurada"]:
        print("\nConfigure as luminárias primeiro (opção 3).")
        return
    n = obter_total_luminarias(ruas)
    consumo_atual = consumo_anual(n, config["potencia_atual"])
    consumo_led = consumo_anual(n, config["potencia_led"])
    reducao = consumo_atual - consumo_led
    economia_energia = reducao * config["tarifa"]
    manutencao = manutencao_evitada(n, config["vida_convencional"], config["custo_troca"])
    investimento = n * config["custo_led"]
    economia_total = economia_energia + manutencao
    payback = payback_simples(investimento, economia_total)

    print("\n=== VIABILIDADE ECONÔMICA ===")
    print(f"Economia de energia no primeiro ano: R$ {economia_energia:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Manutenção evitada estimada por ano: R$ {manutencao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Economia anual total inicial: R$ {economia_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Investimento estimado: R$ {investimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    if payback is None:
        print("Payback simples: não calculável, pois a economia anual não é positiva.")
    else:
        print(f"Payback simples: {payback:.2f} anos — {classificar_payback(payback)}")

    horizonte = int(config["vida_led"] // HORAS_ANO)
    tarifa_ano = config["tarifa"]
    acumulado = 0
    ano_retorno = None
    print(f"\n=== PROJEÇÃO DURANTE {horizonte} ANOS ===")
    print("Ano | Tarifa (R$/kWh) | Economia anual (R$) | Acumulado (R$)")
    economias = []
    for ano in range(1, horizonte + 1):
        economia_ano = reducao * tarifa_ano + manutencao
        acumulado += economia_ano
        economias.append(economia_ano)
        print(f"{ano:>3} | {tarifa_ano:>15.4f} | {economia_ano:>18.2f} | {acumulado:>14.2f}")
        if ano_retorno is None and acumulado >= investimento:
            ano_retorno = ano
        tarifa_ano *= (1 + config["reajuste"] / 100)

    saldo = acumulado - investimento
    if ano_retorno is None:
        print("O investimento não se paga dentro do horizonte considerado.")
    else:
        print(f"A troca se paga no ano {ano_retorno} da projeção.")
    print(f"Economia acumulada: R$ {acumulado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Saldo após descontar o investimento: R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

def relatorio_final(ruas, config):
    if not ruas:
        print("\nCadastre pelo menos uma rua primeiro.")
        return
    print("\n" + "=" * 58)
    print("RELATÓRIO FINAL — ECOLUZ")
    print("=" * 58)
    total = obter_total_luminarias(ruas)
    print(f"Ruas analisadas: {len(ruas)}")
    print(f"Total estimado de postes/luminárias: {total}")
    irregulares = []
    for rua in ruas:
        relacao = relacao_espacamento(rua["espacamento"], rua["altura"])
        if not espacamento_adequado(relacao):
            irregulares.append(rua["nome"])
    print(f"Ruas com espaçamento acima do limite simplificado: {len(irregulares)}")
    if irregulares:
        print("Verificar: " + ", ".join(irregulares))
    if not config["configurada"]:
        print("Configure as luminárias (opção 3) para incluir análise energética e econômica.")
        print("Recomendação: completar os dados antes de decidir sobre a substituição.")
        return

    consumo_atual = consumo_anual(total, config["potencia_atual"])
    consumo_led = consumo_anual(total, config["potencia_led"])
    reducao = consumo_atual - consumo_led
    percentual = (reducao / consumo_atual * 100) if consumo_atual else 0
    economia_energia = reducao * config["tarifa"]
    manutencao = manutencao_evitada(total, config["vida_convencional"], config["custo_troca"])
    investimento = total * config["custo_led"]
    economia_total = economia_energia + manutencao
    payback = payback_simples(investimento, economia_total)
    print(f"Consumo atual: {consumo_atual:.2f} kWh/ano")
    print(f"Consumo com LED: {consumo_led:.2f} kWh/ano")
    print(f"Redução: {reducao:.2f} kWh/ano ({percentual:.1f}%)")
    print(f"Investimento estimado: R$ {investimento:.2f}")
    if payback is not None:
        print(f"Payback simples: {payback:.2f} anos ({classificar_payback(payback)})")
        if percentual > 0 and payback <= 7:
            print("RECOMENDAÇÃO PRELIMINAR: a troca pode ser economicamente interessante no cenário informado.")
        else:
            print("RECOMENDAÇÃO PRELIMINAR: revisar custos, potências e condições antes de recomendar a troca.")
    else:
        print("RECOMENDAÇÃO PRELIMINAR: não recomendada com os valores atuais, pois a economia anual não é positiva.")
    print("\nLimitação: o espaçamento é verificado por regra simplificada; o programa não substitui projeto luminotécnico.")
    print("Os resultados dependem da qualidade dos dados informados.")

def menu():
    ruas = []
    config = {"configurada": False}
    while True:
        print("\n========== ECOLUZ ==========")
        print("1 - Cadastrar as ruas")
        print("2 - Listar as ruas e verificar o espaçamento")
        print("3 - Escolher luminária atual e LED / informar custos")
        print("4 - Comparar o consumo")
        print("5 - Analisar a viabilidade econômica")
        print("6 - Relatório final")
        print("0 - Sair")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_ruas(ruas)
        elif opcao == "2":
            listar_ruas(ruas)
        elif opcao == "3":
            configurar_luminarias(config)
        elif opcao == "4":
            comparar_consumo(ruas, config)
        elif opcao == "5":
            analisar_viabilidade(ruas, config)
        elif opcao == "6":
            relatorio_final(ruas, config)
        elif opcao == "0":
            print("Programa EcoLuz encerrado. Obrigado!")
            break
        else:
            print("Opção inválida. Escolha uma opção do menu.")

if __name__ == "__main__":
    menu()
