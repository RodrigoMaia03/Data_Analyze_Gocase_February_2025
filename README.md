# Business Case Gocase - Análise de Dados de E-commerce

## 1. Visão Geral do Projeto

Este projeto consiste na resolução do Desafio 1 do Business Case para a vaga de Estágio em Inteligência de Dados na Gocase (GoGroup). O objetivo principal é realizar um diagnóstico a partir de bases de dados de Pedidos, Itens e Estoque, transformando dados brutos em insights estratégicos e acionáveis.

Para apresentar os resultados de forma dinâmica e interativa, foi desenvolvido um **Dashboard em Streamlit**, que permite a exploração dos dados e a visualização clara dos principais indicadores de performance da empresa.

---

## 2. Funcionalidades do Dashboard

O dashboard está dividido em seções que abordam as principais áreas do negócio, seguindo as perguntas norteadoras do case e adicionando análises aprofundadas para gerar maior valor.

### Análise de Vendas & Conversão
- **Dashboard de Vendas:** Gráfico interativo com o volume de pedidos ao longo do tempo.
- **Performance de Produtos:** Rankings interativos (Top 10 e Bottom 10) de produtos e categorias por faturamento, com filtro para produtos ativos.
- **Análise de Descontos:** Gráfico de dispersão para visualizar a correlação entre os descontos aplicados e o valor final dos pedidos.
- **Análise de Cesta de Compras:** Ferramenta para selecionar um produto e descobrir os 5 outros itens mais comprados em conjunto.

### Análise de Supply Chain & Estoque
- **Análise de Estoque Crítico:** Tabelas detalhadas que listam produtos em **Ruptura** (estoque zerado) e em **Estado de Alerta** (menos de 7 dias de cobertura), priorizados por impacto de vendas.
- **Eficiência da Reposição:** Histograma que analisa a distribuição do `leadtime` (tempo de reposição), revelando insights sobre a qualidade dos dados de supply.
- **Correlação com Cancelamentos:** Análise aprofundada que compara a taxa de cancelamento entre pedidos com diferentes níveis de risco de supply (Baixo, Médio e Alto).

### Análise de Logística & Entregas
- **Performance Geográfica:** Mapa interativo do Brasil que permite visualizar diferentes KPIs por estado: **Tempo Médio de Entrega**, **Faturamento Total** e **Ticket Médio**.
- **Funil Logístico:** Gráfico de barras empilhadas que decompõe o tempo total de entrega em **Tempo de Preparo** (interno) e **Tempo de Trânsito** (transportadora), identificando gargalos.
- **Performance de Transportadoras (SLA):** Gráfico que mede a taxa de descumprimento de prazo de cada transportadora, identificando os parceiros mais e menos confiáveis.

---

## 3. Como Executar o Projeto

Para visualizar o dashboard interativo em sua máquina, siga os passos abaixo:

**Pré-requisitos:**
- Python 3.8 ou superior
- Pip (gerenciador de pacotes do Python)

**Passos:**

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd [NOME_DO_DIRETORIO]
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    venv\Scripts\activate

    # Ativar no macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    (Certifique-se de que o arquivo `requirements.txt` está no diretório)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Estrutura de Pastas:**
    Certifique-se de que os arquivos de dados (`.xlsx`) estão dentro de uma subpasta chamada `data`.

5.  **Execute a aplicação Streamlit:**
    No terminal, a partir do diretório raiz do projeto, execute:
    ```bash
    streamlit run app.py
    ```
    O dashboard será aberto automaticamente no seu navegador.

---

## 4. Tecnologias Utilizadas

- **Linguagem:** Python
- **Bibliotecas Principais:**
  - **Streamlit:** Para a construção do dashboard web interativo.
  - **Pandas:** Para manipulação, limpeza e análise dos dados.
  - **Plotly Express:** Para a criação dos gráficos interativos e visualizações de dados.
  - **Requests:** Para a requisição inicial do arquivo GeoJSON.

---

## 5. Autor

**[Seu Nome Completo]**

- [Link para seu LinkedIn]
- [Link para seu GitHub]
