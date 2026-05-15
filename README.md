# Re Leve Ops AI - Protótipo Interativo

Este pacote contém um dashboard interativo em Streamlit para apresentar a solução do Grupo 3, com foco em melhoria de eficiência operacional da Re Leve Recife.

## O que está incluído

- `app.py`: aplicação principal do dashboard.
- `requirements.txt`: bibliotecas necessárias.
- `data/dados_pedidos_base_final.xlsx`: base de pedidos.
- `data/fatura_do_cartao (Custo Variavel).csv`: base de custos variáveis.
- `.streamlit/config.toml`: tema visual do dashboard.
- `run_local.bat`: execução rápida no Windows.
- `run_local.sh`: execução rápida no Mac/Linux.

## Como rodar na sua máquina

### Passo 1 - Instalar o Python
Baixe e instale o Python em https://www.python.org/downloads/.
Durante a instalação no Windows, marque a opção **Add Python to PATH**.

### Passo 2 - Abrir a pasta do projeto
Descompacte este arquivo ZIP e entre na pasta `releve_ops_ai`.

### Passo 3 - Instalar as dependências
No terminal, dentro da pasta do projeto, execute:

```bash
python -m pip install -r requirements.txt
```

### Passo 4 - Rodar o dashboard
Execute:

```bash
streamlit run app.py
```

O navegador abrirá automaticamente com o dashboard.

## Como publicar na web gratuitamente

1. Crie uma conta no GitHub.
2. Crie um repositório chamado `releve-ops-ai`.
3. Envie todos os arquivos desta pasta para o repositório.
4. Acesse https://streamlit.io/cloud.
5. Clique em **New app**.
6. Escolha o repositório `releve-ops-ai`.
7. Em **Main file path**, informe `app.py`.
8. Clique em **Deploy**.

Você receberá um link público para apresentar ao cliente.

## Roteiro recomendado para apresentação

1. Abra com o problema: a Re Leve quer crescer, mas a operação é enxuta.
2. Mostre os dados recebidos: pedidos, custos e presença digital.
3. Apresente o dashboard como solução prática.
4. Demonstre os KPIs principais: pedidos, faturamento, ticket médio e média diária.
5. Mostre os gráficos de demanda e horário de pico.
6. Explique os insights de IA e alertas operacionais.
7. Mostre a previsão de demanda.
8. Finalize com o plano de ação e o impacto esperado.

## Frase de impacto

"Criamos um copiloto operacional para transformar dados da Re Leve em decisões rápidas sobre produção, custos e eficiência, reduzindo desperdícios e aumentando a capacidade de escala da operação."
