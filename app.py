import streamlit as st
import pandas as pd
import os
import plotly.express as px
from io import StringIO
import json

# Infos da Página
st.set_page_config(
    page_title="Gocase Business Case",
    page_icon="🏁",
    layout="wide"
)
st.title("📊 Análise de Dados - Business Case Gocase")
st.markdown("Análise dos dados de Vendas, Estoque e Logística no mês de Fevereiro de 2025.")

# Carregamento dos Dados
@st.cache_data
def carregar_dados():
    """Carrega os dados das planilhas, aplicando cache para melhorar performance."""
    caminho_pedidos = os.path.join('data', 'Case Dados - Pedidos.xlsx')
    caminho_itens_supply = os.path.join('data', 'Business Case Dados - Itens + Supply.xlsx')
    try:
        df_pedidos = pd.read_excel(caminho_pedidos)
        df_itens = pd.read_excel(caminho_itens_supply, sheet_name='Itens')
        df_supply = pd.read_excel(caminho_itens_supply, sheet_name='Supply')
        return df_pedidos, df_itens, df_supply
    except FileNotFoundError:
        st.error("Erro: Arquivos de dados não encontrados. Verifique se eles estão na pasta 'data'.")
        return None, None, None

df_pedidos_raw, df_itens_raw, df_supply_raw = carregar_dados()

# --- Bloco Principal: Executado apenas se os dados forem carregados corretamente ---
if df_pedidos_raw is not None:
    # Pré-processamento: Remove Colunas Desnecessárias
    st.success("Dados carregados! Otimizando e iniciando o pré-processamento...")

    # Copia para manter os dataframes originais intactos
    df_pedidos = df_pedidos_raw.copy()
    df_itens = df_itens_raw.copy()
    df_supply = df_supply_raw.copy()

    # Removeção de colunas desnecessárias
    colunas_remover_pedidos = ['Código de Rastreio', 'CEP', 'postage_list_id', 'Peso (kg)']
    colunas_remover_itens = ['material_weight_kg', 'aasm_state', 'reprint_batch_id', 'supply_paid', 'stock_burning', 'consumable_letters']
    colunas_remover_supply = ['factory_id', 'reposition', 'inventory_center_id', 'material_localization_id']
    df_pedidos.drop(columns=colunas_remover_pedidos, inplace=True, errors='ignore')
    df_itens.drop(columns=colunas_remover_itens, inplace=True, errors='ignore')
    df_supply.drop(columns=colunas_remover_supply, inplace=True, errors='ignore')

    # Renomeação de colunas para facilitar a análise
    mapa_nomes_pedidos = {
        'id': 'id_pedido', 'reference': 'numero_referencia', 'created_at': 'data_pedido',
        'Valor de NF (R$)': 'valor_nf', 'order_state': 'estado_pedido_interno', 'Cidade': 'cidade', 
        'Estado': 'estado', 'Frete Cobrado do Cliente (R$)': 'frete_cliente',
        'Frete cobrado pela transportadora (R$)': 'frete_transportadora',
        'Transportadora': 'transportadora', 'Número da NF': 'numero_nf', 
        'Status do Pedido': 'status_pedido', 'Prazo para Sair do CD': 'prazo_saida_cd', 
        'Enviado em:': 'data_envio', 'Entregue para o cliente em:': 'data_entrega',
        'Prazo a transportadora entregar no cliente': 'prazo_entrega_transportadora',
        'Número de Itens no Pedido': 'numero_itens'
    }
    df_pedidos.rename(columns=mapa_nomes_pedidos, inplace=True)
    df_itens.rename(columns={'order_id': 'id_pedido'}, inplace=True)
    df_supply.rename(columns={'quantity': 'estoque_disponivel'}, inplace=True)

    # Normalização de colunas
    df_pedidos['id_pedido'] = pd.to_numeric(df_pedidos['id_pedido'], errors='coerce')
    df_pedidos.dropna(subset=['id_pedido'], inplace=True)
    df_pedidos['id_pedido'] = df_pedidos['id_pedido'].astype(int)

    #  Normalização de datas, valores numéricos e criação de novas colunas
    data_pedido_norm = pd.to_datetime(df_pedidos['data_pedido'], errors='coerce').dt.normalize()
    data_entrega_norm = pd.to_datetime(df_pedidos['data_entrega'], errors='coerce').dt.normalize()
    df_pedidos['tempo_entrega_dias'] = (data_entrega_norm - data_pedido_norm).dt.days
    df_pedidos['data_pedido'] = pd.to_datetime(df_pedidos['data_pedido'], errors='coerce')
    df_pedidos['ano_mes'] = df_pedidos['data_pedido'].dt.to_period('M').astype(str)
    df_itens['id_pedido'] = pd.to_numeric(df_itens['id_pedido'], errors='coerce')
    df_itens['price'] = pd.to_numeric(df_itens['price'], errors='coerce').fillna(0)
    df_itens['quantidade'] = 1

    # Junção (Merge) das Bases
    df_supply_agg = df_supply.groupby('material_id').agg({
        'estoque_disponivel': 'sum', 'discontinued': 'first', 'leadtime': 'mean'
    }).reset_index()
    df_itens_supply = pd.merge(
        left=df_itens, right=df_supply_agg, on='material_id', how='left'
    )
    df_completo = pd.merge(
        left=df_pedidos, right=df_itens_supply, on='id_pedido', how='left'
    )
    df_completo['material_name'].fillna('Não informado', inplace=True)
    st.success("Bases de dados otimizadas, tratadas e unificadas!")
    
    # --- INÍCIO DAS SEÇÕES DE ANÁLISE ---

    # 1. ANÁLISE DE VENDAS & CONVERSÃO 
    st.header("1. Análise de Vendas & Conversão")
    st.subheader("Distribuição de Pedidos ao Longo do Tempo")
    
    # Análise de pedidos por dia
    pedidos_por_dia = df_completo.drop_duplicates(subset='id_pedido').set_index('data_pedido').resample('D').agg({'id_pedido': 'count'}).reset_index()
    pedidos_por_dia.rename(columns={'id_pedido': 'quantidade_pedidos'}, inplace=True)
    fig_vendas_tempo = px.line(
        pedidos_por_dia, x='data_pedido', y='quantidade_pedidos', title='Volume de Pedidos por Dia',
        labels={'data_pedido': 'Data', 'quantidade_pedidos': 'Número de Pedidos'}
    )
    fig_vendas_tempo.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig_vendas_tempo, use_container_width=True)
    st.markdown("---")

    if 'faturamento_item' not in df_completo.columns:
        df_completo['faturamento_item'] = df_completo['quantidade'] * df_completo['price']

    # Análise dos produtos/categorias com maior impacto no faturamento
    st.subheader("Produtos e Categorias de Maior Impacto no Faturamento (Top 10)")
    visao_top = st.selectbox("Visualizar por:", ("Produto", "Categoria"), key='select_top')

    if visao_top == "Categoria":
        top_data = df_completo.groupby('material_category')['faturamento_item'].sum().sort_values(ascending=False).reset_index().head(10)
        top_data_sorted = top_data.sort_values(by='faturamento_item', ascending=False)
        fig_top = px.bar(
            top_data_sorted, y='faturamento_item', x='material_category', title="Top 10 Categorias por Faturamento",
            text_auto='.2s', labels={'faturamento_item': 'Faturamento (R$)', 'material_category': 'Categoria'}
        )
    else: # Visão por Produto
        top_10_produtos = df_completo.groupby('material_name')['faturamento_item'].sum().nlargest(10).reset_index()
        top_data_sorted = top_10_produtos.sort_values(by='faturamento_item', ascending=True).copy()
        top_data_sorted['nome_curto'] = top_data_sorted['material_name'].apply(lambda x: (x[:45] + '...') if len(x) > 45 else x)
        
        fig_top = px.bar(
            top_data_sorted,
            x='faturamento_item', 
            y='nome_curto', 
            title="Top 10 Produtos por Faturamento",
            text_auto='.2s', 
            hover_name='material_name', 
            labels={'faturamento_item': 'Faturamento (R$)', 'nome_curto': 'Produto'}
        )

    st.plotly_chart(fig_top, use_container_width=True)
    st.markdown("---")

    # Análise dos produtos com menor impacto no faturamento
    st.subheader("Produtos e Categorias de Menor Impacto no Faturamento (Bottom 10)")
    st.markdown("Análise dos **produtos ativos** com menor performance de vendas. Itens descontinuados são desconsiderados.")

    # Cria um DataFrame contendo apenas produtos ativos
    df_ativo = df_completo[df_completo['discontinued'].fillna(False) == False]

    visao_bottom = st.selectbox("Visualizar por:", ("Produto", "Categoria"), key='select_bottom')
    if visao_bottom == "Categoria":
        bottom_data = df_ativo[df_ativo['faturamento_item'] > 0].groupby('material_category')['faturamento_item'].sum().sort_values(ascending=True).reset_index().head(10)
        fig_bottom = px.bar(
            bottom_data, x='material_category', y='faturamento_item', title="Top 10 Categorias Ativas com Menor Faturamento",
            text_auto='.2s', labels={'faturamento_item': 'Faturamento (R$)', 'material_category': 'Categoria'}
        )
        fig_bottom.update_layout(xaxis={'categoryorder':'total ascending'})
    else:
        bottom_data = df_ativo[df_ativo['faturamento_item'] > 0].groupby('material_name')['faturamento_item'].sum().sort_values(ascending=True).reset_index().head(10).copy()
        bottom_data['nome_curto'] = bottom_data['material_name'].apply(lambda x: (x[:35] + '...') if len(x) > 35 else x)
        fig_bottom = px.bar(
            bottom_data, x='faturamento_item', y='nome_curto', title="Top 10 Produtos Ativos com Menor Faturamento",
            text_auto='.2s', hover_name='material_name', labels={'faturamento_item': 'Faturamento (R$)', 'nome_curto': 'Produto'}
        )
        fig_bottom.update_layout(yaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_bottom, use_container_width=True)
    st.markdown("---")
    
    # Análise da tendência de itens que são comprados conjuntamente
    st.subheader("Análise de Cesta de Compras (Produtos Comprados Juntos)")
    st.markdown("Selecione um produto específico para descobrir quais outros itens são mais frequentemente comprados junto com ele.")

    top_produtos_lista = df_completo['material_name'].value_counts().nlargest(50).index.tolist()
    produto_selecionado = st.selectbox(
        "Selecione um produto de referência:",
        top_produtos_lista
    )

    if produto_selecionado:
        # Encontra todos os pedidos que contêm o produto selecionado
        pedidos_com_produto = df_completo[df_completo['material_name'] == produto_selecionado]['id_pedido'].unique()
        itens_dos_pedidos_relevantes = df_completo[df_completo['id_pedido'].isin(pedidos_com_produto)]
        
        # Conta a frequência de todos os outros produtos comprados nesses pedidos
        produtos_associados = itens_dos_pedidos_relevantes[
            itens_dos_pedidos_relevantes['material_name'] != produto_selecionado
        ]['material_name'].value_counts().head(5)

        if not produtos_associados.empty:
            produtos_associados_df = produtos_associados.reset_index()
            produtos_associados_df.columns = ['produto_associado', 'contagem']
            produtos_associados_df['nome_curto'] = produtos_associados_df['produto_associado'].apply(lambda x: (x[:45] + '...') if len(x) > 45 else x)

            st.markdown(f"##### Top 5 produtos mais comprados junto com:")
            st.info(f"{produto_selecionado}")
            
            fig_cesta = px.bar(
                produtos_associados_df,
                x='contagem',
                y='nome_curto',
                orientation='h',
                title=f"Produtos Comprados com o item selecionado",
                labels={'contagem': 'Pedidos em Comum', 'nome_curto': 'Produto Associado'},
                text='contagem',
                hover_name='produto_associado'
            )
            fig_cesta.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_cesta, use_container_width=True)

        else:
            st.warning(f"Não foram encontrados outros produtos comprados frequentemente junto com este item.")
    st.markdown("---")

    # Análise do impacto dos descontos nos valores dos pedidos
    st.subheader("Relação entre Descontos e Valor do Pedido")
    agg_pedidos = df_completo.groupby('id_pedido').agg(
        subtotal_calculado=('faturamento_item', 'sum'),
        quantidade_itens=('quantidade', 'sum')
    ).reset_index()
    dados_nf = df_completo[['id_pedido', 'valor_nf']].drop_duplicates()
    analise_desconto = pd.merge(agg_pedidos, dados_nf, on='id_pedido')
    analise_desconto['desconto_calculado'] = analise_desconto['subtotal_calculado'] - analise_desconto['valor_nf']
    analise_desconto_filtrado = analise_desconto[
        (analise_desconto['desconto_calculado'] >= 0) &
        (analise_desconto['desconto_calculado'] < (analise_desconto['subtotal_calculado'] * 0.95))
    ]
    fig_desconto = px.scatter(
        analise_desconto_filtrado, x='desconto_calculado', y='valor_nf', title='Valor do Pedido vs. Desconto Aplicado (Dados Filtrados)',
        labels={'desconto_calculado': 'Desconto Inferido (R$)', 'valor_nf': 'Valor da Nota Fiscal (R$)'},
        trendline='ols', hover_data=['quantidade_itens']
    )
    if len(fig_desconto.data) > 1:
        fig_desconto.data[1].line.color = 'red'
    st.plotly_chart(fig_desconto, use_container_width=True)
    st.markdown("---")

    # 2. ANÁLISE DE SUPPLY CHAIN & ESTOQUE
    st.header("2. Análise de Supply Chain & Estoque")
    st.subheader("Análise de Estoque Crítico")
    st.markdown("Listas detalhadas de produtos que necessitam de atenção imediata da equipe de suprimentos. **Produtos descontinuados são desconsiderados.**")
    
    # Cria um DataFrame contendo apenas produtos ativos
    df_ativo = df_completo[df_completo['discontinued'].fillna(False) == False].copy()

    # Verifica se há dados de produtos ativos para análise e realiza a análise de cobertura de estoque
    if not df_ativo.empty:
        dias_analise = (df_ativo['data_pedido'].max() - df_ativo['data_pedido'].min()).days
        if dias_analise == 0: dias_analise = 1

        vendas_por_id = df_ativo.groupby('material_id')['quantidade'].sum().reset_index()
        vendas_por_id.rename(columns={'quantidade': 'vendas_totais'}, inplace=True)
        vendas_por_id['media_vendas_diaria'] = vendas_por_id['vendas_totais'] / dias_analise

        estoque_por_id = df_ativo[['material_id', 'material_name', 'estoque_disponivel']].drop_duplicates(subset='material_id')
        analise_cobertura = pd.merge(vendas_por_id, estoque_por_id, on='material_id')
        
        analise_cobertura['estoque_disponivel'].fillna(0, inplace=True)
        analise_cobertura['dias_cobertura'] = (
            analise_cobertura['estoque_disponivel'] / (analise_cobertura['media_vendas_diaria'] + 0.0001)
        ).round(0).astype(int)

        produtos_criticos = analise_cobertura[analise_cobertura['media_vendas_diaria'] > 0].sort_values(
            by=['dias_cobertura', 'media_vendas_diaria'], ascending=[True, False]
        )

        tab_ruptura, tab_critico_total = st.tabs(["🚨 Produtos em Ruptura (Estoque Zerado)", "⚠️ Todos em Estado Crítico (< 7 dias)"])

        # Exibe os produtos em ruptura (estoque zerado)
        with tab_ruptura:
            st.markdown("Estes são os produtos com **vendas recentes** mas com **estoque zerado**. A lista está ordenada pelo produto de maior impacto (maior média de vendas).")
            df_ruptura = produtos_criticos[produtos_criticos['dias_cobertura'] == 0]
            styled_ruptura = df_ruptura[['material_id', 'material_name', 'media_vendas_diaria']].style.format({'media_vendas_diaria': "{:.2f}"})
            st.dataframe(styled_ruptura)

        # Exibe todos os produtos críticos com menos de 7 dias de cobertura
        with tab_critico_total:
            st.markdown("Esta lista inclui **todos** os produtos com menos de 7 dias de cobertura de estoque, ordenada pelos mais críticos e de maior impacto.")
            df_critico_completo = produtos_criticos[produtos_criticos['dias_cobertura'] < 7]
            styled_critico_total = df_critico_completo[['material_id', 'material_name', 'estoque_disponivel', 'media_vendas_diaria', 'dias_cobertura']].style.format({
                'estoque_disponivel': "{:.2f}", 'media_vendas_diaria': "{:.2f}"
            }).apply(lambda x: ['background-color: #FF7F7F' if x.dias_cobertura < 7 else '' for i in x], axis=1)
            st.dataframe(styled_critico_total)
        st.markdown("---")
    else:
        st.warning("Não foram encontrados dados de produtos ativos para análise de estoque.")

    # Análise de Lead Time
    st.subheader("Distribuição do Tempo de Reposição (Lead Time)")
    st.markdown("O histograma abaixo mostra a frequência dos diferentes tempos de reposição para os produtos ativos.")
    leadtime_data = df_supply_agg[df_supply_agg['leadtime'] > 0]
    
    # Verifica se há dados de leadtime disponíveis antes de plotar o histograma
    if not leadtime_data.empty:
        fig_leadtime_hist = px.histogram(
            leadtime_data, x="leadtime", nbins=30, title="Frequência de Produtos por Tempo de Reposição",
            labels={"leadtime": "Lead Time (dias)"}
        )
        fig_leadtime_hist.update_yaxes(title_text="Frequência")
        st.plotly_chart(fig_leadtime_hist, use_container_width=True)
        st.markdown("---")
    else:
        st.warning("Não foram encontrados dados de 'leadtime' para análise.")

    # Análise de Correlação entre Estoque Crítico e Cancelamentos
    st.subheader("Correlação entre Estoque Crítico e Cancelamentos")
    st.markdown("Análise aprimorada com **níveis de risco** para investigar se a gravidade do problema de estoque influencia a taxa de cancelamento.")

    # Separa IDs de produtos em 'Ruptura' (estoque=0) e 'Alerta' (estoque baixo)
    ids_ruptura = produtos_criticos[produtos_criticos['dias_cobertura'] == 0]['material_id'].unique()
    ids_alerta = produtos_criticos[(produtos_criticos['dias_cobertura'] > 0) & (produtos_criticos['dias_cobertura'] < 7)]['material_id'].unique()

    # Marca cada item no DataFrame principal com seu nível de risco
    df_completo['risco_item'] = 'Baixo'
    df_completo.loc[df_completo['material_id'].isin(ids_alerta), 'risco_item'] = 'Médio (Alerta)'
    df_completo.loc[df_completo['material_id'].isin(ids_ruptura), 'risco_item'] = 'Alto (Ruptura)'

    # Determina o nível de risco máximo para cada pedido
    df_completo['risco_num'] = df_completo['risco_item'].map({'Baixo': 0, 'Médio (Alerta)': 1, 'Alto (Ruptura)': 2})
    risco_por_pedido = df_completo.groupby('id_pedido')['risco_num'].max().reset_index()
    risco_map_inverso = {0: 'Baixo', 1: 'Médio (Alerta)', 2: 'Alto (Ruptura)'}
    risco_por_pedido['nivel_risco_pedido'] = risco_por_pedido['risco_num'].map(risco_map_inverso)

    # Identifica pedidos cancelados
    status_cancelado = 'canceled'
    df_pedidos_status = df_completo[['id_pedido', 'status_pedido']].drop_duplicates()
    df_pedidos_status['foi_cancelado'] = (df_pedidos_status['status_pedido'] == status_cancelado)

    # Junta as informações de risco e cancelamento
    analise_corr_refinada = pd.merge(risco_por_pedido, df_pedidos_status[['id_pedido', 'foi_cancelado']], on='id_pedido')

    # Calcula a taxa de cancelamento por nível de risco
    taxa_cancelamento_por_risco = analise_corr_refinada.groupby('nivel_risco_pedido')['foi_cancelado'].mean().reset_index()
    taxa_cancelamento_por_risco['taxa_percentual'] = (taxa_cancelamento_por_risco['foi_cancelado'] * 100)

    st.markdown("##### Comparativo da Taxa de Cancelamento por Nível de Risco de Supply")
    ordem_risco = ['Baixo', 'Médio (Alerta)', 'Alto (Ruptura)']
    fig_corr_refinada = px.bar(
        taxa_cancelamento_por_risco,
        x='nivel_risco_pedido',
        y='taxa_percentual',
        color='nivel_risco_pedido',
        category_orders={'nivel_risco_pedido': ordem_risco}, 
        title='Taxa de Cancelamento por Nível de Risco do Pedido',
        labels={'nivel_risco_pedido': 'Nível de Risco de Supply', 'taxa_percentual': 'Taxa de Cancelamento (%)'},
        text='taxa_percentual'
    )
    fig_corr_refinada.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    st.plotly_chart(fig_corr_refinada, use_container_width=True)

    st.markdown("""
    **Análise Aprimorada:** Comparamos a taxa de cancelamento entre três grupos de pedidos.
    - **Risco Baixo:** Nosso grupo de controle, com produtos de estoque saudável.
    - **Risco Médio:** Pedidos com itens que estão prestes a acabar.
    - **Risco Alto:** Pedidos com itens já esgotados.
    """)

    # 3. ANÁLISE DE LOGÍSTICA & ENTREGAS
    st.header("3. Análise de Logística & Entregas")

    st.subheader("Análise Geográfica de Performance")
    st.markdown("Use o seletor para alterar a métrica exibida no mapa e comparar a performance logística e de vendas entre os estados.")
    df_logistica = df_completo.drop_duplicates(subset='id_pedido').copy()
    df_logistica_valid_time = df_logistica[df_logistica['tempo_entrega_dias'] >= 0]

    # Seleciona a métrica para visualização
    metrica_selecionada = st.selectbox(
        "Selecione a Métrica para Visualizar:",
        ["Tempo Médio de Entrega", "Faturamento Total", "Ticket Médio"]
    )

    # Prepara o DataFrame de acordo com a métrica selecionada
    if metrica_selecionada == "Tempo Médio de Entrega":
        df_mapa = df_logistica_valid_time.groupby('estado')['tempo_entrega_dias'].mean().round(1).reset_index()
        coluna_cor = 'tempo_entrega_dias'
        escala_cor = 'YlOrRd' # Amarelo para Vermelho (pior)
        label_cor = 'Entrega (dias)'

    elif metrica_selecionada == "Faturamento Total":
        df_mapa = df_logistica.groupby('estado')['valor_nf'].sum().reset_index()
        coluna_cor = 'valor_nf'
        escala_cor = 'Blues' # Tons de Azul (melhor)
        label_cor = 'Faturamento (R$)'

    else: # Ticket Médio
        df_mapa = df_logistica.groupby('estado')['valor_nf'].mean().reset_index()
        coluna_cor = 'valor_nf'
        escala_cor = 'Greens' # Tons de Verde (melhor)
        label_cor = 'Ticket Médio (R$)'

    # Mapea os estados para suas siglas
    mapa_estados = {
        'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA',
        'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO',
        'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
        'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI',
        'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS',
        'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP',
        'Sergipe': 'SE', 'Tocantins': 'TO'
    }
    df_mapa['sigla'] = df_mapa['estado'].map(mapa_estados)
    df_mapa.dropna(subset=['sigla'], inplace=True)

    # Carrega o GeoJSON dos estados brasileiros
    caminho_geojson = os.path.join('data', 'brazil_states.geojson')
    try:
        with open(caminho_geojson, "r", encoding='utf-8') as f:
            geojson_br = json.load(f)
        
        # 6. Criar o mapa de calor dinâmico
        if not df_mapa.empty:
            fig_mapa = px.choropleth(
                df_mapa,
                geojson=geojson_br,
                locations='sigla',
                featureidkey="properties.sigla",
                color=coluna_cor,
                color_continuous_scale=escala_cor,
                hover_name='estado',
                hover_data={coluna_cor: ':.2f'},
                labels={coluna_cor: label_cor}
            )
            
            fig_mapa.update_geos(
                visible=False, center={"lat": -14, "lon": -55},
                lataxis_range=[-34, 6], lonaxis_range=[-74, -34]
            )
            fig_mapa.update_layout(
                title_text=f"{metrica_selecionada} por Estado",
                margin={"r":0,"t":40,"l":0,"b":0}
            )
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.error("A tabela de dados para o mapa está vazia.")

    except FileNotFoundError:
        st.error(f"Arquivo 'brazil_states.geojson' não encontrado na pasta 'data'.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o mapa: {e}")

    st.markdown("---")

    # Análise do Funil Logístico
    st.subheader("Análise do Funil Logístico por Transportadora")
    st.markdown("Decompomos o tempo total de entrega para identificar onde estão os maiores gargalos: no preparo interno do pedido ou no transporte.")

    # Normaliza todas as datas para garantir consistência
    df_funil = df_completo.drop_duplicates(subset='id_pedido').copy()
    df_funil['data_pedido_norm'] = pd.to_datetime(df_funil['data_pedido']).dt.normalize()
    df_funil['data_envio_norm'] = pd.to_datetime(df_funil['data_envio']).dt.normalize()
    df_funil['data_entrega_norm'] = pd.to_datetime(df_funil['data_entrega']).dt.normalize()
    df_funil['tempo_preparo'] = (df_funil['data_envio_norm'] - df_funil['data_pedido_norm']).dt.days
    df_funil['tempo_transito'] = (df_funil['data_entrega_norm'] - df_funil['data_envio_norm']).dt.days

    # Evita valores negativos que podem ocorrer devido a erros de data
    df_funil = df_funil[(df_funil['tempo_preparo'] >= 0) & (df_funil['tempo_transito'] >= 0)]

    # Calcula a média de cada etapa por transportadora
    funil_por_transportadora = df_funil.groupby('transportadora').agg({
        'tempo_preparo': 'mean',
        'tempo_transito': 'mean'
    }).reset_index()

    # Prepara os dados para o gráfico de barras empilhadas, renomeia as colunas e cria o gráfico
    df_melted = pd.melt(
        funil_por_transportadora, 
        id_vars='transportadora', 
        value_vars=['tempo_preparo', 'tempo_transito'],
        var_name='etapa',
        value_name='dias'
    )

    mapa_legenda = {
        'tempo_preparo': 'Tempo de Preparo',
        'tempo_transito': 'Tempo de Trânsito'
    }
    df_melted['etapa'] = df_melted['etapa'].map(mapa_legenda)

    fig_funil = px.bar(
        df_melted,
        x='transportadora',
        y='dias',
        color='etapa',
        title='Tempo Médio de Preparo vs. Trânsito por Transportadora',
        labels={'transportadora': 'Transportadora', 'dias': 'Tempo Médio (dias)', 'etapa': 'Etapa do Pedido'},
        text='dias'
    )
    
    fig_funil.update_traces(texttemplate='%{text:.1f}', textposition='inside')
    st.plotly_chart(fig_funil, use_container_width=True)

    st.markdown("""
    **Análise Inicial:** O gráfico de barras empilhadas mostra o tempo total de entrega dividido entre as duas principais etapas.
    - **Tempo de Preparo:** Reflete a eficiência operacional interna da Gocase.
    - **Tempo de Trânsito:** Reflete a performance da transportadora.
    """)
    st.markdown("---")
    
    # Análise de Cancelamentos e Atrasos na Entrega
    st.subheader("Análise de Cancelamentos e Atrasos na Entrega")
    st.markdown("##### Taxa Geral de Cancelamento")

    # Calcula a taxa de cancelamento geral
    pedidos_unicos = df_completo.drop_duplicates(subset='id_pedido')
    total_pedidos = len(pedidos_unicos)
    pedidos_cancelados = len(pedidos_unicos[pedidos_unicos['status_pedido'] == 'canceled'])
    taxa_cancelamento_geral = (pedidos_cancelados / total_pedidos) * 100

    st.metric(label="Taxa de Cancelamento Geral", value=f"{taxa_cancelamento_geral:.2f}%")

    st.markdown("##### Possíveis Causas: Cancelamento por Transportadora")
    st.markdown("Analisamos a taxa de cancelamento para cada transportadora para identificar se alguma apresenta uma performance inferior.")

    # Calcula a taxa de cancelamento por transportadora
    cancel_por_transportadora = df_completo.groupby('transportadora')['status_pedido'].apply(
        lambda x: (x == 'canceled').sum() / len(x) * 100
    ).sort_values(ascending=False).reset_index(name='taxa_cancelamento')

    # Filtra as transportadoras com volume relevante de pedidos para uma análise mais justa
    transportadoras_relevantes = df_completo['transportadora'].value_counts()
    cancel_por_transportadora = cancel_por_transportadora[
        cancel_por_transportadora['transportadora'].isin(transportadoras_relevantes[transportadoras_relevantes > 50].index)
    ]

    fig_cancel_transportadora = px.bar(
        cancel_por_transportadora,
        x='transportadora',
        y='taxa_cancelamento',
        title='Taxa de Cancelamento (%) por Transportadora',
        labels={'transportadora': 'Transportadora', 'taxa_cancelamento': 'Taxa de Cancelamento (%)'},
        text='taxa_cancelamento'
    )
    fig_cancel_transportadora.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    st.plotly_chart(fig_cancel_transportadora, use_container_width=True)
    st.markdown("---")

    # Análise de Atrasos na Entrega
    st.markdown("##### Padrões de Atraso na Entrega")
    st.markdown("Analisamos o tempo médio de entrega por dia da semana e por categoria de produto. **Use o filtro abaixo para analisar uma transportadora específica.**")

    # Caixade seleção para filtrar por transportadora
    lista_transportadoras = ['Todas'] + sorted(df_logistica['transportadora'].dropna().unique().tolist())
    transportadora_selecionada = st.selectbox(
        "Filtrar por Transportadora:",
        lista_transportadoras
    )

    # Filtra os DataFrames com base na seleção
    if transportadora_selecionada == 'Todas':
        df_logistica_filtrado = df_logistica
        df_completo_filtrado = df_completo
    else:
        df_logistica_filtrado = df_logistica[df_logistica['transportadora'] == transportadora_selecionada]
        df_completo_filtrado = df_completo[df_completo['transportadora'] == transportadora_selecionada]

    # Análise por Dia da Semana
    if not df_logistica_filtrado.empty:
        df_logistica_filtrado = df_logistica_filtrado.copy()
        df_logistica_filtrado['dia_semana_num'] = df_logistica_filtrado['data_pedido'].dt.dayofweek
        dias_semana_map = {
            0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 
            3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
        }
        df_logistica_filtrado['dia_semana_nome'] = df_logistica_filtrado['dia_semana_num'].map(dias_semana_map)

        atraso_por_dia_semana = df_logistica_filtrado.groupby(['dia_semana_num', 'dia_semana_nome'])['tempo_entrega_dias'].mean().reset_index()

        fig_atraso_dia_semana = px.bar(
            atraso_por_dia_semana.sort_values('dia_semana_num'),
            x='dia_semana_nome', y='tempo_entrega_dias',
            title=f'Tempo Médio de Entrega por Dia da Semana ({transportadora_selecionada})',
            labels={'dia_semana_nome': 'Dia da Semana', 'tempo_entrega_dias': 'Tempo Médio de Entrega (dias)'},
            text='tempo_entrega_dias'
        )
        fig_atraso_dia_semana.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        st.plotly_chart(fig_atraso_dia_semana, use_container_width=True)
    else:
        st.warning(f"Não há dados de entrega para a transportadora '{transportadora_selecionada}'.")

    # Análise por Categoria de Produto
    if not df_completo_filtrado.empty:
        atraso_por_categoria = df_completo_filtrado[df_completo_filtrado['tempo_entrega_dias'] >= 0].groupby('material_category')['tempo_entrega_dias'].mean().sort_values(ascending=False).reset_index()

        fig_atraso_categoria = px.bar(
            atraso_por_categoria.head(10), x='tempo_entrega_dias', y='material_category',
            title=f'Top 10 Categorias com Maior Tempo de Entrega ({transportadora_selecionada})',
            labels={'material_category': 'Categoria do Produto', 'tempo_entrega_dias': 'Tempo Médio de Entrega (dias)'},
            text='tempo_entrega_dias'
        )
        fig_atraso_categoria.update_traces(texttemplate='%{text:.1f}', textposition='inside')
        fig_atraso_categoria.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_atraso_categoria, use_container_width=True)
    
    # Análise de SLA (Service Level Agreement) das Transportadoras
    st.subheader("Performance de Entrega das Transportadoras (SLA)")
    st.markdown("Analisamos a porcentagem de entregas realizadas fora do prazo prometido por cada transportadora.")

    # Dados necessários para análise de SLA
    df_prazos = df_completo[['id_pedido', 'transportadora', 'data_entrega', 'prazo_entrega_transportadora']].drop_duplicates(subset='id_pedido').copy()
    df_prazos.dropna(subset=['data_entrega', 'prazo_entrega_transportadora'], inplace=True)

    # Normaliza as datas para comparação justa
    df_prazos['data_entrega_norm'] = pd.to_datetime(df_prazos['data_entrega']).dt.normalize()
    df_prazos['prazo_entrega_norm'] = pd.to_datetime(df_prazos['prazo_entrega_transportadora']).dt.normalize()

    # Identifica entregas atrasadas
    df_prazos['atrasado'] = df_prazos['data_entrega_norm'] > df_prazos['prazo_entrega_norm']

    # Calcula a taxa de atraso por transportadora
    sla_transportadora = df_prazos.groupby('transportadora').agg(
        total_entregas=('id_pedido', 'count'),
        entregas_atrasadas=('atrasado', 'sum')
    ).reset_index()
    sla_transportadora['taxa_atraso_%'] = (sla_transportadora['entregas_atrasadas'] / sla_transportadora['total_entregas'] * 100)

    fig_sla = px.bar(
        sla_transportadora.sort_values('taxa_atraso_%', ascending=False),
        x='transportadora',
        y='taxa_atraso_%',
        title='Taxa de Atraso na Entrega (%) por Transportadora',
        labels={'transportadora': 'Transportadora', 'taxa_atraso_%': 'Taxa de Atraso (%)'},
        text='taxa_atraso_%',
        hover_data=['entregas_atrasadas', 'total_entregas']
    )
    fig_sla.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    st.plotly_chart(fig_sla, use_container_width=True)