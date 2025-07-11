import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re # Importar para a limpeza de caracteres
import os # Importar para caminhos de arquivo

# --- Configuração da página Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard de Análise de Jogos")

st.title("🎮 Dashboard de Análise de Jogos 🎮")
st.markdown("Explore dados sobre lançamentos, gêneros, desenvolvedores e preços de jogos.")

# --- Carregar e Preparar os Dados (Diretamente no Streamlit) ---
@st.cache_data(show_spinner="Carregando e processando dados base...") # Cachear com spinner
def load_and_preprocess_data():
    """Carrega o dataset e realiza todas as etapas de pré-processamento."""
    try:
        # ATENÇÃO: Verifique o nome do seu arquivo CSV.
        df = pd.read_csv('DB_completo.csv')
    except FileNotFoundError:
        st.error("ERRO: O arquivo CSV ('DB.csv') não encontrado. Por favor, certifique-se de que o arquivo está na mesma pasta do script.")
        st.stop()

    df.drop_duplicates(inplace=True)

    # Limpeza de caracteres não ASCII para evitar erros de codificação em gráficos
    def remove_non_ascii(text):
        if isinstance(text, str):
            return re.sub(r'[^\x00-\x7F]+', '', text)
        return text

    df['title'] = df['title'].apply(remove_non_ascii)
    df['platform'] = df['platform'].apply(remove_non_ascii)
    df['developers'] = df['developers'].apply(remove_non_ascii)
    df['publishers'] = df['publishers'].apply(remove_non_ascii)

    genre_columns = [col for col in df.columns if col.startswith('genre_')]
    df['genre_list'] = df.apply( # Renomeado para genre_list para evitar confusão com 'genre' da explosão
        lambda row: [col.replace('genre_', '') for col in genre_columns if row[col]],
        axis=1
    )
    # Se a lista de gêneros for vazia, atribui ['Desconhecido']
    df['genre_list'] = df['genre_list'].apply(lambda x: x if x else ['Desconhecido'])

    # Converter a lista de gêneros para tupla para melhorar o hashing do Pandas (útil para cache)
    df['genre_list'] = df['genre_list'].apply(tuple)

    # Processamento de Datas
    df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce').fillna(0).astype(int)
    df['release_month'] = pd.to_numeric(df['release_month'], errors='coerce').fillna(1).astype(int)
    df['release_date'] = pd.to_datetime(
        df['release_year'].astype(str) + '-' +
        df['release_month'].astype(str).str.zfill(2) + '-01',
        errors='coerce'
    )
    df.dropna(subset=['release_date'], inplace=True) # Remover linhas com datas inválidas

    # Definir Períodos da Pandemia baseando-se nas datas
    pandemic_start_date = pd.Timestamp('2020-04-01')
    pandemic_end_date = pd.Timestamp('2022-03-31')
    post_pandemic_start_date = pd.Timestamp('2022-04-01')

    def assign_period_with_dates(date):
        if date < pandemic_start_date:
            return 'Pré-Pandemia'
        elif pandemic_start_date <= date <= pandemic_end_date:
            return 'Pandemia'
        elif date >= post_pandemic_start_date:
            return 'Pós-Pandemia'
        return 'Desconhecido'

    df['periodo'] = df['release_date'].apply(assign_period_with_dates)

    # Garantir colunas de preço numéricas e preencher NaNs
    df['preco_dolar'] = pd.to_numeric(df['preco_dolar'], errors='coerce')
    df['preco_euro'] = pd.to_numeric(df['preco_euro'], errors='coerce')
    df.dropna(subset=['preco_dolar', 'preco_euro'], inplace=True)

    # Corrigir nomes de colunas e preencher NaNs para 'developers' e 'platform'
    df['developers'] = df['developers'].fillna('Desconhecido')
    df['platform'] = df['platform'].fillna('Outra')

    # Obter anos mínimo e máximo do dataset completo
    min_overall_year = int(df['release_year'].min())
    max_overall_year = int(df['release_year'].max())

    return df, min_overall_year, max_overall_year

# Carrega e pré-processa os dados base
df_main, min_overall_year, max_overall_year = load_and_preprocess_data()
#st.sidebar.success("Dados base carregados e pré-processados!")

# Criando duas colunas na barra lateral
col1, col2 = st.sidebar.columns(2)

# Inserindo as imagens nas colunas
with col1:
    st.image("ufrn.png", width=150)

with col2:
    st.image("dca.png", width=100)

# --- Filtros Globais na Barra Lateral ---
st.sidebar.header("Filtros Globais")

# Filtro Global de Plataforma
all_platforms = ['Todas'] + sorted(df_main['platform'].unique().tolist())
selected_platform_global = st.sidebar.selectbox("Filtrar por Plataforma:", all_platforms, key='global_platform')

# Filtro Global de Gênero
# Para o multiselect de gênero, precisamos dos gêneros únicos do df principal, não do explodido
all_genres_from_main = set()
for genres_tuple in df_main['genre_list']:
    for genre_item in genres_tuple:
        all_genres_from_main.add(genre_item)
all_genres_global_options = ['Todos'] + sorted(list(all_genres_from_main))
selected_genre_global = st.sidebar.multiselect("Filtrar por Gênero:", all_genres_global_options, default=all_genres_global_options, key='global_genre')

# Filtros Globais de Período da Pandemia
selected_pandemic_periods_global = st.sidebar.multiselect(
    "Período da Pandemia:",
    options=['Pré-Pandemia', 'Pandemia', 'Pós-Pandemia'],
    default=['Pré-Pandemia', 'Pandemia', 'Pós-Pandemia'],
    key='global_pandemic_periods'
)

# --- Função para aplicar TODOS os filtros globais (Plataforma, Gênero, Período, Ano) ---
@st.cache_data(show_spinner="Aplicando filtros e preparando dados para gráficos...")
def apply_all_global_filters(df_base, platform_filter, genre_filter, pandemic_periods_filter, current_years_filter):
    df_filtered = df_base.copy()

    # 1. Filtrar por Plataforma
    if platform_filter != 'Todas':
        df_filtered = df_filtered[df_filtered['platform'] == platform_filter]

    # 2. Filtrar por Período da Pandemia
    if pandemic_periods_filter:
        df_filtered = df_filtered[df_filtered['periodo'].isin(pandemic_periods_filter)]
    else:
        st.warning("Nenhum 'Período da Pandemia' selecionado nos filtros globais. Isso pode resultar em dados vazios.")
        return pd.DataFrame(), pd.DataFrame(), None, None # Retorna DFs vazios e None para anos

    # 3. Filtrar por Gênero (usando 'genre_list' para jogos com múltiplos gêneros)
    if genre_filter and 'Todos' not in genre_filter:
        df_filtered = df_filtered[
            df_filtered['genre_list'].apply(lambda genres_in_row_tuple: any(g_in_row in genre_filter for g_in_row in genres_in_row_tuple))
        ]

    # Calcular o range de anos dinâmico *APÓS* os filtros de plataforma, gênero e pandemia
    if not df_filtered.empty:
        dynamic_min_year_calculated = int(df_filtered['release_year'].min())
        dynamic_max_year_calculated = int(df_filtered['release_year'].max())
    else:
        # Se os filtros anteriores resultarem em DataFrame vazio, use o range geral para o slider
        dynamic_min_year_calculated = min_overall_year
        dynamic_max_year_calculated = max_overall_year

    # Aplicar filtro de range de anos
    min_year_slider, max_year_slider = current_years_filter
    df_filtered = df_filtered[
        (df_filtered['release_year'] >= min_year_slider) &
        (df_filtered['release_year'] <= max_year_slider)
    ]

    # Agora, e SOMENTE AGORA, explodimos para a versão por gênero se necessário
    # Crie df_genres_exploded_filtered aqui
    if not df_filtered.empty:
        df_genres_exploded_filtered = df_filtered.explode('genre_list')
        df_genres_exploded_filtered.rename(columns={'genre_list': 'genre'}, inplace=True)
    else:
        df_genres_exploded_filtered = pd.DataFrame() # Retorna DF vazio se o original for vazio

    return df_filtered, df_genres_exploded_filtered, dynamic_min_year_calculated, dynamic_max_year_calculated

# --- Lógica do Slider de Ano e Reaplicação dos Filtros ---
# Esta parte é um pouco complexa devido à natureza do Streamlit e o slider dinâmico.
# Precisamos de um valor inicial para o slider ANTES de aplicar o filtro de ano,
# e depois ajustá-lo com base nos dados filtrados pelos outros critérios.

# Primeiro, obtenha o range dinâmico baseado nos filtros de plataforma/gênero/pandemia (sem o filtro de ano)
df_temp_for_year_range, _, dynamic_min_year_calculated_initial, dynamic_max_year_calculated_initial = apply_all_global_filters(
    df_main, selected_platform_global, selected_genre_global, selected_pandemic_periods_global,
    (min_overall_year, max_overall_year) # Passa o range completo temporariamente
)

# Definir os limites min/max do slider
slider_min_val = dynamic_min_year_calculated_initial if dynamic_min_year_calculated_initial is not None else min_overall_year
slider_max_val = dynamic_max_year_calculated_initial if dynamic_max_year_calculated_initial is not None else max_overall_year

# Garantir que o valor padrão do slider esteja dentro dos limites atuais
default_slider_val = st.session_state.get('global_years', (slider_min_val, slider_max_val))
adjusted_default_min = max(slider_min_val, default_slider_val[0])
adjusted_default_max = min(slider_max_val, default_slider_val[1])
if adjusted_default_min > adjusted_default_max: # Corrige caso o range fique invertido
    adjusted_default_min = slider_min_val
    adjusted_default_max = slider_max_val
initial_slider_value_for_display = (adjusted_default_min, adjusted_default_max)


selected_years_global = st.sidebar.slider(
    'Intervalo de Anos:',
    min_value=slider_min_val,
    max_value=slider_max_val,
    value=initial_slider_value_for_display,
    key='global_years' # Keep the same key for the slider
)

# RE-APLICAR todos os filtros, agora com o valor FINAL do slider de anos
df_global_filtered, df_genres_global_filtered, _, _ = apply_all_global_filters(
    df_main, selected_platform_global, selected_genre_global, selected_pandemic_periods_global, selected_years_global
)

# --- Geração e Exibição dos Gráficos com Plotly.express em ABAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Visão Geral de Lançamentos e Gêneros",
    "Análise por Plataforma e Desenvolvedor",
    "Distribuição de Preços e Tendências",
    "Tendências de Lançamento por Período",
    "Visão Hierárquica",
    "Heatmap de Preços",
    "Info Adicional"
])


# --- TAB 1: Visão Geral de Lançamentos e Gêneros ---
with tab1:
    st.header("Visão Geral de Lançamentos e Gêneros")
    df_tab_current = df_genres_global_filtered # Esta aba usa o df com gêneros explodidos

    if not df_tab_current.empty:
        with st.spinner("Carregando Gráficos da Visão Geral..."):
            with st.container():
                col4, col5, col6 = st.columns(3)
                with col4:
                    st.subheader("1. Jogos Lançados por Ano")
                    df_jogos_por_ano = df_tab_current.groupby('release_year').size().reset_index(name='count')
                    if not df_jogos_por_ano.empty:
                        fig1 = px.bar(df_jogos_por_ano, x='release_year', y='count', title='Jogos Lançados por Ano')
                        fig1.update_xaxes(dtick=1, tickformat="%Y")
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Nenhum dado de jogos lançados por ano com os filtros selecionados.")
                with col5:
                    st.subheader("2. Top 10 Gêneros por Número de Lançamentos")
                    df_generos_count = df_tab_current['genre'].value_counts().nlargest(10).reset_index()
                    df_generos_count.columns = ['genre', 'count']
                    if not df_generos_count.empty:
                        fig2 = px.bar(df_generos_count, x='genre', y='count',
                                        title='Top 10 Gêneros por Número de Lançamentos')
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Nenhum dado de top 10 gêneros com os filtros selecionados.")
                with col6:
                    st.subheader("3. Distribuição de Preços por Gênero")
                    if not df_tab_current.empty:
                        top_genres = df_tab_current['genre'].value_counts().nlargest(10).index
                        df_price_genre = df_tab_current[df_tab_current['genre'].isin(top_genres)]

                        if not df_price_genre.empty:
                            fig3 = px.box(df_price_genre, x='genre', y='preco_dolar',
                                            title='Distribuição de Preços (Dólar) por Gênero (Top 10)',
                                            labels={'preco_dolar': 'Preço (Dólar)'},
                                            height=500)
                            st.plotly_chart(fig3, use_container_width=True)
                        else:
                            st.info("Nenhum dado de distribuição de preços por gênero com os filtros selecionados.")
                    else:
                        st.info("Nenhum dado de distribuição de preços por gênero com os filtros selecionados.")
    else:
        st.info("Nenhum dado para exibir na Visão Geral de Lançamentos e Gêneros com os filtros globais selecionados.")


# --- Tab 2: Análise por Plataforma e Desenvolvedor ---
with tab2:
    st.header("Análise por Plataforma e Desenvolvedor")
    df_tab_current = df_global_filtered # Esta aba usa o df principal filtrado

    if not df_tab_current.empty:
        with st.spinner("Carregando Gráficos de Plataforma e Desenvolvedor..."):
            # Gráfico 4: Lançamentos por Plataforma ao Longo do Tempo (Gráfico de Linha)
            st.subheader("4. Lançamentos por Plataforma ao Longo do Tempo")
            df_platform_releases_over_time = df_tab_current.groupby(['release_year', 'platform']).size().reset_index(name='count')
            if not df_platform_releases_over_time.empty:
                fig4 = px.line(df_platform_releases_over_time, x='release_year', y='count', color='platform',
                                title='Lançamentos por Plataforma ao Longo do Tempo',
                                labels={'release_year': 'Ano de Lançamento', 'count': 'Número de Lançamentos'})
                fig4.update_xaxes(dtick=1, tickformat="%Y")
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Nenhum dado de lançamentos por plataforma ao longo do tempo com os filtros selecionados.")

            # Gráfico 5: Top 10 Desenvolvedores por Número de Lançamentos
            st.subheader("5. Top 10 Desenvolvedores por Número de Lançamentos")
            top_n_devs = st.slider("Mostrar Top N Desenvolvedores:", 5, 20, 10, key='top_devs_tab2')

            df_dev_count = df_tab_current['developers'].value_counts().nlargest(top_n_devs).reset_index()
            df_dev_count.columns = ['developers', 'count']
            if not df_dev_count.empty:
                fig5 = px.bar(df_dev_count, x='developers', y='count',
                                title=f'Top {top_n_devs} Desenvolvedores por Número de Lançamentos')
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info("Nenhum dado de top desenvolvedores com os filtros selecionados.")

            # Gráfico 6: Distribuição de Preços por Plataforma (Box Plot)
            st.subheader("6. Distribuição de Preços por Plataforma")
            if not df_tab_current.empty:
                top_platforms = df_tab_current['platform'].value_counts().nlargest(10).index
                df_price_platform = df_tab_current[df_tab_current['platform'].isin(top_platforms)]

                if not df_price_platform.empty:
                    fig6 = px.box(df_price_platform, x='platform', y='preco_dolar',
                                    title='Distribuição de Preços (Dólar) por Plataforma (Top 10)',
                                    labels={'preco_dolar': 'Preço (Dólar)'},
                                    height=500)
                    st.plotly_chart(fig6, use_container_width=True)
                else:
                    st.info("Nenhum dado de distribuição de preços por plataforma com os filtros selecionados.")
            else:
                st.info("Nenhum dado de distribuição de preços por plataforma com os filtros selecionados.")
    else:
        st.info("Nenhum dado para exibir na Análise por Plataforma e Desenvolvedor com os filtros globais selecionados.")


# --- Tab 3: Distribuição de Preços e Tendências ---
with tab3:
    st.header("Distribuição de Preços e Tendências")

    st.markdown("Selecione a base de dados para a análise de preços:")
    st.markdown("- **Uma Entrada por Jogo:** Cada jogo aparece uma vez, mesmo se tiver múltiplos gêneros. Ideal para contagens de jogos ou análises gerais de preço por jogo.")
    st.markdown("- **Uma Entrada por Gênero do Jogo:** Um jogo com múltiplos gêneros (ex: Ação e Aventura) aparece uma vez para Ação e outra para Aventura. Ideal para análises que focam em cada gênero individualmente (ex: preço médio de 'Ação').")

    price_analysis_base_selection = st.radio(
        "Base de Dados:",
        ('Uma Entrada por Jogo', 'Uma Entrada por Gênero do Jogo'),
        key='price_analysis_base_tab3'
    )

    df_tab_current = df_global_filtered if price_analysis_base_selection == 'Uma Entrada por Jogo' else df_genres_global_filtered

    if not df_tab_current.empty:
        with st.spinner("Carregando Gráficos de Distribuição de Preços e Tendências..."):
            # Gráfico 7: Histograma Geral de Preços em Dólar
            st.subheader("7. Histograma Geral de Preços em Dólar")
            if not df_tab_current.empty:
                fig7 = px.histogram(df_tab_current, x='preco_dolar', nbins=50,
                                    title='Distribuição de Preços em Dólar',
                                    labels={'preco_dolar': 'Preço (Dólar)'})
                st.plotly_chart(fig7, use_container_width=True)
            else:
                st.info("Nenhum dado de histograma geral de preços com os filtros selecionados.")

            # Gráfico 8: Tendência de Preços Médios ao Longo do Tempo (por Plataforma ou Gênero)
            st.subheader("8. Tendência de Preços Médios ao Longo do Tempo")
            trend_by_option_tab8 = st.selectbox(
                "Analisar tendência de preço por:",
                ('Plataforma', 'Gênero'),
                key='trend_option_tab8'
            )

            if not df_tab_current.empty:
                if trend_by_option_tab8 == 'Plataforma':
                    df_line_chart_data = df_tab_current.groupby(['release_year', 'platform'])['preco_dolar'].mean().reset_index()
                    color_by_line = 'platform'
                    title_suffix_line = 'por Plataforma'
                else: # trend_by_option_tab8 == 'Gênero'
                    # Certificar-se de usar df_genres_global_filtered para análise por Gênero
                    df_line_chart_data = df_genres_global_filtered.groupby(['release_year', 'genre'])['preco_dolar'].mean().reset_index()
                    color_by_line = 'genre'
                    title_suffix_line = 'por Gênero'

                if not df_line_chart_data.empty:
                    fig8 = px.line(
                        df_line_chart_data,
                        x='release_year',
                        y='preco_dolar',
                        color=color_by_line,
                        title=f'Tendência de Preços Médios {title_suffix_line}',
                        labels={'release_year': 'Ano de Lançamento', 'preco_dolar': 'Preço Médio (Dólar)'},
                        height=500
                    )
                    fig8.update_xaxes(dtick=1, tickformat="%Y", showgrid=True)
                    st.plotly_chart(fig8, use_container_width=True)
                else:
                    st.info("Nenhum dado para exibir para a Tendência de Preços com os filtros selecionados.")
            else:
                st.info("Nenhum dado para exibir para a Tendência de Preços com os filtros selecionados.")
    else:
        st.info("Nenhum dado para exibir na Distribuição de Preços e Tendências com os filtros globais selecionados.")

# --- Tab 4: Tendências de Lançamento por Período ---
with tab4:
    st.header("Tendências de Lançamento por Período")
    df_tab_current = df_genres_global_filtered # Esta aba usa o df com gêneros explodidos

    if not df_tab_current.empty:
        with st.spinner("Carregando Gráficos de Tendências de Lançamento por Período..."):
            # Gráfico 9: Lançamentos Anuais por Gênero (Gráfico de Barras Empilhadas)
            st.subheader("9. Lançamentos Anuais por Gênero")
            df_genre_releases_annual = df_tab_current.groupby(['release_year', 'genre']).size().reset_index(name='count')
            if not df_genre_releases_annual.empty:
                fig9 = px.bar(df_genre_releases_annual, x='release_year', y='count', color='genre',
                                title='Lançamentos Anuais por Gênero',
                                labels={'release_year': 'Ano de Lançamento', 'count': 'Número de Lançamentos'},
                                hover_name='genre')
                fig9.update_xaxes(dtick=1, tickformat="%Y")
                st.plotly_chart(fig9, use_container_width=True)
            else:
                st.info("Nenhum dado de lançamentos anuais por gênero com os filtros selecionados.")

            # Gráfico 10: Top 5 Gêneros por Período de Lançamento (Comparativo)
            st.subheader("10. Top 5 Gêneros por Período de Lançamento (Comparativo)")
            df_genre_period = df_tab_current.groupby(['periodo', 'genre']).size().reset_index(name='count')

            if not df_genre_period.empty:
                # Lógica corrigida para obter Top N por grupo, preservando a coluna 'periodo'
                top_genres_by_period = df_genre_period.sort_values(by=['periodo', 'count'], ascending=[True, False]) \
                                                        .groupby('periodo') \
                                                        .head(5)

                if not top_genres_by_period.empty:
                    fig10 = px.bar(top_genres_by_period, x='genre', y='count', color='periodo', # 'periodo' agora está presente
                                    barmode='group',
                                    title='Top Gêneros por Período de Lançamento',
                                    labels={'genre': 'Gênero', 'count': 'Número de Lançamentos', 'periodo': 'Período'},
                                    height=500)
                    st.plotly_chart(fig10, use_container_width=True)
                else:
                    st.info("Nenhum dado de top gêneros por período para exibir com os filtros selecionados.")
            else:
                st.info("Nenhum dado de top gêneros por período para exibir com os filtros selecionados.")
    else:
        st.info("Nenhum dado para exibir nas Tendências de Lançamento por Período com os filtros globais selecionados.")


# --- Tab 5: Visão Hierárquica ---
with tab5:
    st.header("Visão Hierárquica")
    st.markdown("Explore a distribuição de jogos hierarquicamente.")
    df_tab_current = df_genres_global_filtered # Esta aba usa o df com gêneros explodidos

    if not df_tab_current.empty:
        with st.spinner("Carregando Gráficos da Visão Hierárquica..."):
            col_s1, col_s2 = st.columns(2)

            # Gráfico Sunburst para Gênero -> Plataforma -> Número de Lançamentos
            with col_s1:
                st.subheader("11. Gênero -> Plataforma (Lançamentos)")
                df_sunburst1 = df_tab_current.groupby(['genre', 'platform']).size().reset_index(name='count')
                if not df_sunburst1.empty:
                    fig11 = px.sunburst(df_sunburst1, path=['genre', 'platform'], values='count',
                                        title='Distribuição de Lançamentos por Gênero e Plataforma')
                    st.plotly_chart(fig11, use_container_width=True)
                else:
                    st.info("Nenhum dado para o Sunburst Gênero -> Plataforma com os filtros selecionados.")

            # Gráfico Sunburst para Período -> Gênero -> Número de Lançamentos
            with col_s2:
                st.subheader("12. Período -> Gênero (Lançamentos)")
                df_sunburst2_agg = df_tab_current.groupby(['periodo', 'genre']).size().reset_index(name='count')
                if not df_sunburst2_agg.empty:
                    fig12 = px.sunburst(df_sunburst2_agg, path=['periodo', 'genre'], values='count',
                                        title='Distribuição de Lançamentos por Período e Gênero')
                    st.plotly_chart(fig12, use_container_width=True)
                else:
                    st.info("Nenhum dado para o Sunburst Período -> Gênero com os filtros selecionados.")

            st.markdown("---") # Divisor visual
            col_s3, col_s4 = st.columns(2)

            # Gráfico Sunburst para Desenvolvedor -> Gênero -> Número de Lançamentos
            with col_s3:
                st.subheader("13. Desenvolvedor -> Gênero (Lançamentos)")
                df_sunburst3 = df_tab_current.groupby(['developers', 'genre']).size().reset_index(name='count')
                if not df_sunburst3.empty:
                    fig13 = px.sunburst(df_sunburst3, path=['developers', 'genre'], values='count',
                                        title='Distribuição de Lançamentos por Desenvolvedor e Gênero')
                    st.plotly_chart(fig13, use_container_width=True)
                else:
                    st.info("Nenhum dado para o Sunburst Desenvolvedor -> Gênero com os filtros selecionados.")

            # Gráfico Sunburst para Gênero -> Preço Médio (Total)
            with col_s4:
                st.subheader("14. Gênero -> Preço Médio (Total)")
                df_sunburst4 = df_tab_current.groupby('genre')['preco_dolar'].sum().reset_index()
                if not df_sunburst4.empty:
                    fig14 = px.sunburst(df_sunburst4, path=['genre'], values='preco_dolar',
                                        title='Total de Preços (Dólar) por Gênero')
                    st.plotly_chart(fig14, use_container_width=True)
                else:
                    st.info("Nenhum dado para o Sunburst Gênero -> Preço Médio com os filtros selecionados.")

    else:
        st.info("Nenhum dado para exibir na Visão Hierárquica com os filtros globais selecionados.")

# --- Tab 6: Heatmap de Preços ---
with tab6:
    st.header("Heatmap de Preços Médios por Gênero e Ano")
    st.markdown("Visualize o preço médio dos jogos por gênero em diferentes anos.")
    df_tab_current = df_genres_global_filtered # Esta aba usa o df com gêneros explodidos

    if not df_tab_current.empty:
        with st.spinner("Carregando Heatmap de Preços Médios..."):
            df_heatmap_data = df_tab_current.groupby(['release_year', 'genre'])['preco_dolar'].mean().reset_index()
            if not df_heatmap_data.empty:
                fig_heatmap = px.density_heatmap(
                    df_heatmap_data,
                    x='release_year',
                    y='genre',
                    z='preco_dolar',
                    title='Preço Médio por Gênero e Ano',
                    labels={'release_year': 'Ano de Lançamento', 'genre': 'Gênero', 'preco_dolar': 'Preço Médio (Dólar)'},
                    height=600,
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                fig_heatmap.update_xaxes(dtick=1, tickformat="%Y")
                fig_heatmap.update_yaxes(categoryorder='total ascending')
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("Nenhum dado para o Heatmap de Preços com os filtros selecionados.")
    else:
        st.info("Nenhum dado para exibir no Heatmap de Preços com os filtros globais selecionados.")

# --- Tab 7: Informações Adicionais (Pode ser removida se não for usada) ---
with tab7:
    st.header("Informações Adicionais")
    st.write("Esta aba pode ser usada para adicionar informações sobre o projeto, dados ou outras explicações.")
    st.markdown("""
        **Desenvolvimento:** Este dashboard foi desenvolvido como parte de um projeto de análise de dados.
        **Fonte dos Dados:** Dados fictícios/sintéticos para fins demonstrativos.
        **Contato:** [Seu Nome/Email/LinkedIn]
    """)

st.sidebar.markdown("---")
st.sidebar.info(
    "Este dashboard interativo permite explorar dados de jogos, incluindo tendências de lançamento, "
    "preferências de gênero, atividades de desenvolvedores e distribuição de preços."
)