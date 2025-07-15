
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os
import base64
import joblib 
import numpy as np 
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report 
import matplotlib.pyplot as plt 
import seaborn as sns
from forex_python.converter import CurrencyRates
import datetime

# --- Configuração da página Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard de Análise de Jogos")

# --- Adicionar Imagem de Fundo (App e Sidebar) ---
background_image_app_path = "Background_app.jpg" # Imagem para o fundo do app
background_image_sidebar_path = "background_sidebar.jpg" # Imagem para o fundo da sidebar

# Função para ler e codificar a imagem em base64
@st.cache_data
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# Obter imagens codificadas
encoded_background_app = get_base64_image(background_image_app_path)
encoded_background_sidebar = get_base64_image(background_image_sidebar_path)

# String de CSS para aplicar os estilos
css_string = """
<style>
/* Estilo para o fundo principal do aplicativo */
"""
if encoded_background_app:
    css_string += f"""
    .stApp {{
        background-image: url("data:image/jpeg;base64,{encoded_background_app}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    """
else:
    st.warning(f"A imagem de fundo do app '{background_image_app_path}' não foi encontrada.")

css_string += """
/* Estilo para o fundo da sidebar */
"""
if encoded_background_sidebar:
    css_string += f"""
    .stSidebar {{
        background-image: url("data:image/jpeg;base64,{encoded_background_sidebar}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    """
else:
    st.warning(f"A imagem de fundo da sidebar '{background_image_sidebar_path}' não foi encontrada.")

css_string += """
/* Ajustes de cor do texto para melhor legibilidade */
.stMarkdown, .stText, .stHeader, .stSubheader, .stTitle, .stLabel,
.stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label,
.stButton, .stProgress, .stExpander {
    color: white; 
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
}
/* Ajustar a cor de fundo dos elementos internos do app principal */
.css-1fv8s86, .css-1dp5vir {
    background-color: rgba(0, 0, 0, 0.5);
    padding: 20px;
    border-radius: 10px;
}
/* Ajustar a cor de fundo dos elementos internos da sidebar */
.stSidebar > div:first-child {
    background-color: rgba(0, 0, 0, 0.6);
    padding: 10px;
    border-radius: 10px;
}
.stSidebar .stSelectbox > div > div, .stSidebar .stMultiSelect > div > div {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 5px;
}
/* Ajustes para as imagens da UFRN/DCA */
.stSidebar img {
    background-color: transparent;
}
</style>
"""
st.markdown(css_string, unsafe_allow_html=True)


st.title("🎮 Dashboard de Análise de Jogos 🎮")
st.markdown("Explore dados sobre lançamentos, gêneros, desenvolvedores e preços de jogos.")


# --- FUNÇÃO DE CARREGAMENTO E PRÉ-PROCESSAMENTO DE DADOS ---
@st.cache_data(show_spinner="Carregando e processando dados base...")
def load_and_preprocess_data():
    """Carrega o dataset, realiza o pré-processamento e retorna o dataframe e os anos min/max."""
    colunas_com_aviso = {
        'genre_Action': 'boolean', 'genre_Adventure': 'boolean', 'genre_Indie': 'boolean', 
        'genre_RPG': 'boolean', 'genre_Simulation': 'boolean', 'genre_Sports': 'boolean', 
        'genre_Strategy': 'boolean'
    }
    try:
        df = pd.read_csv('DB_completo.csv', dtype=colunas_com_aviso)
    except FileNotFoundError:
        st.error("ERRO: O arquivo 'DB_completo.csv' não foi encontrado. Certifique-se de que ele está na mesma pasta.")
        st.stop()

    df.drop_duplicates(inplace=True)

    def remove_non_ascii(text):
        if isinstance(text, str): return re.sub(r'[^\x00-\x7F]+', '', text)
        return text

    text_cols = ['title', 'platform', 'developers', 'publishers']
    for col in text_cols: df[col] = df[col].apply(remove_non_ascii)
    
    genre_columns = [col for col in df.columns if col.startswith('genre_')]
    df['genre_list'] = df.apply(lambda row: [col.replace('genre_', '') for col in genre_columns if pd.notna(row[col]) and row[col]], axis=1)
    df['genre_list'] = df['genre_list'].apply(lambda x: x if x else ['Desconhecido']).apply(tuple)

    df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce').fillna(0).astype(int)
    df['release_month'] = pd.to_numeric(df['release_month'], errors='coerce').fillna(1).astype(int)
    df['release_date'] = pd.to_datetime(
        df['release_year'].astype(str) + '-' + df['release_month'].astype(str).str.zfill(2) + '-01',
        errors='coerce'
    )
    df.dropna(subset=['release_date'], inplace=True)

    pandemic_start_date = pd.Timestamp('2020-04-01')
    pandemic_end_date = pd.Timestamp('2022-03-31')
    
    def assign_period_with_dates(date):
        if date < pandemic_start_date: return 'Pré-Pandemia'
        if pandemic_start_date <= date <= pandemic_end_date: return 'Pandemia'
        return 'Pós-Pandemia'
    
    df['periodo'] = df['release_date'].apply(assign_period_with_dates)

    price_cols = ['preco_dolar', 'preco_euro']
    for col in price_cols: df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=price_cols, inplace=True)

    df['developers'] = df['developers'].fillna('Desconhecido')
    df['platform'] = df['platform'].fillna('Outra')

    min_overall_year = int(df['release_year'].min())
    max_overall_year = int(df['release_year'].max())
    
    return df, min_overall_year, max_overall_year


@st.cache_data(ttl=14400) # Cache por 14400 segundos = 4 horas
def obter_cotacao_dolar():
    """Busca a cotação USD para BRL e armazena em cache."""
    try:
        c = CurrencyRates()
        taxa = c.get_rate('USD', 'BRL')
        return taxa
    except Exception as e:
        st.error(f"Não foi possível obter a cotação do dólar. Erro: {e}")
        return None # Retorna None em caso de erro


# --- LÓGICA PRINCIPAL DE CARREGAMENTO E FILTROS ---

# 1. Carrega e pré-processa os dados base do CSV
df_main, min_overall_year, max_overall_year = load_and_preprocess_data()

# 2. Carrega TODOS os modelos e colunas de arquivos .joblib separados
# Modelo de Classificação
modelo_classificacao = None
colunas_classificacao = None
try:
    modelo_classificacao = joblib.load('modelo_classificacao_jogos.joblib')
    colunas_classificacao = joblib.load('colunas_classificacao_jogos.joblib')
except FileNotFoundError as e:
    st.sidebar.error(f"Arquivo de CLASSIFICAÇÃO não encontrado: {e.filename}.")
except Exception as e:
    st.sidebar.error(f"Erro ao carregar arquivos de classificação: {e}")

# Modelo de Regressão
modelo_regressao = None
colunas_regressao = None
try:
    modelo_regressao = joblib.load('modelo_regressao_preco.joblib')
    colunas_regressao = joblib.load('colunas_regressao_preco.joblib')
except FileNotFoundError as e:
    st.sidebar.error(f"Arquivo de REGRESSÃO não encontrado: {e.filename}.")
except Exception as e:
    st.sidebar.error(f"Erro ao carregar arquivos de regressão: {e}")

if modelo_classificacao is not None and colunas_classificacao is not None and modelo_regressao is not None and colunas_regressao is not None:
    st.sidebar.success("Todos os modelos foram carregados!")

# 3. Pré-calcula variáveis para as abas de predição
dev_popularity = df_main['developers'].value_counts()
pub_popularity = df_main['publishers'].value_counts()
all_genres_list = sorted(list(set(g for genres_tuple in df_main['genre_list'] for g in genres_tuple if g != 'Desconhecido')))

# --- Conteúdo da Barra Lateral (Sidebar) ---
with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.image("ufrn.png", width=150)
    with col2:
        st.image("dca.png", width=100)

    st.header("Filtros Globais")

    # Filtro de Plataforma
    all_platforms = ['Todas'] + sorted(df_main['platform'].unique().tolist())
    selected_platform_global = st.selectbox("Plataforma:", all_platforms, key='global_platform')

    # Filtro de Gênero
    all_genres_from_main = sorted(list(set(g for genres_tuple in df_main['genre_list'] for g in genres_tuple)))
    selected_genre_global = st.multiselect("Gênero(s):", ['Todos'] + all_genres_from_main, default=['Todos'], key='global_genre')
    if not selected_genre_global: selected_genre_global = ['Todos'] # Garante que não fique vazio

    # Filtro de Período
    selected_pandemic_periods_global = st.multiselect(
        "Período:",
        options=['Pré-Pandemia', 'Pandemia', 'Pós-Pandemia'],
        default=['Pré-Pandemia', 'Pandemia', 'Pós-Pandemia'],
        key='global_pandemic_periods'
    )

@st.cache_data(show_spinner="Aplicando filtros e preparando dados...")
def apply_all_global_filters(df_base, platform_filter, genre_filter, pandemic_periods_filter, years_filter):
    """Aplica todos os filtros da sidebar e retorna os dataframes filtrados."""
    df_filtered = df_base.copy()

    if platform_filter != 'Todas':
        df_filtered = df_filtered[df_filtered['platform'] == platform_filter]

    if pandemic_periods_filter:
        df_filtered = df_filtered[df_filtered['periodo'].isin(pandemic_periods_filter)]

    if 'Todos' not in genre_filter and genre_filter:
        df_filtered = df_filtered[df_filtered['genre_list'].apply(lambda genres: any(g in genre_filter for g in genres))]

    if not df_filtered.empty:
        df_filtered = df_filtered[(df_filtered['release_year'] >= years_filter[0]) & (df_filtered['release_year'] <= years_filter[1])]

    df_genres_exploded = df_filtered.explode('genre_list').rename(columns={'genre_list': 'genre'}) if not df_filtered.empty else pd.DataFrame(columns=df_filtered.columns.tolist() + ['genre'])
    
    return df_filtered, df_genres_exploded

# --- Lógica do Slider de Ano Dinâmico ---
with st.sidebar:
    # Filtra temporariamente para obter o range de anos dinâmico
    temp_genres_filter = [] if 'Todos' in selected_genre_global else selected_genre_global
    temp_filtered_df, _ = apply_all_global_filters(
        df_main, selected_platform_global, temp_genres_filter, selected_pandemic_periods_global,
        (min_overall_year, max_overall_year)
    )
    
    if not temp_filtered_df.empty:
        dynamic_min_year = int(temp_filtered_df['release_year'].min())
        dynamic_max_year = int(temp_filtered_df['release_year'].max())
    else:
        dynamic_min_year, dynamic_max_year = min_overall_year, max_overall_year

    # Slider de ano
    if dynamic_min_year > dynamic_max_year: # Prevenção de erro
        dynamic_min_year = dynamic_max_year
        
    selected_years_global = st.slider(
        'Intervalo de Anos:',
        min_value=dynamic_min_year,
        max_value=dynamic_max_year,
        value=(dynamic_min_year, dynamic_max_year),
        key='global_years'
    )

# Aplica os filtros finais com o valor do slider de ano
df_global_filtered, df_genres_global_filtered = apply_all_global_filters(
    df_main, selected_platform_global, selected_genre_global, selected_pandemic_periods_global, selected_years_global
)



# --- Geração e Exibição dos Gráficos com Plotly.express em ABAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab_matriz, tab_predicao, tab_pred_avancada = st.tabs([
    "Visão Geral de Lançamentos e Gêneros",
    "Análise por Plataforma e Desenvolvedor",
    "Distribuição de Preços e Tendências",
    "Tendências de Lançamento por Período",
    "Visão Hierárquica",
    "Heatmap de Preços",
    "Matriz de confusão do modelo",
    "Predição Simples",
    "Predição Avançada"
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

with tab_matriz:
    st.header("🔮 Avaliação do Modelo de Classificação")
    st.markdown("O modelo é aplicado aos dados **filtrados na barra lateral** para gerar métricas de desempenho em tempo real.")

    # CORREÇÃO: Usar os nomes de variáveis corretos 'modelo_classificacao' e 'colunas_classificacao'
    if modelo_classificacao is not None and colunas_classificacao is not None and not df_global_filtered.empty:
        with st.spinner("Avaliando modelo nos dados filtrados..."):
            df_eval = df_global_filtered.copy()

            bins = [0, 15, 45, np.inf]
            labels = ['Barato', 'Médio', 'Caro']
            df_eval['faixa_preco'] = pd.cut(df_eval['preco_dolar'], bins=bins, labels=labels, right=False)
            df_eval.dropna(subset=['faixa_preco'], inplace=True)

            if df_eval.empty:
                st.warning("Nenhum jogo nos dados filtrados se encaixa nas faixas de preço para avaliação.")
            else:
                y_true = df_eval['faixa_preco']
                cols_to_drop = [
                    'preco_dolar', 'preco_euro', 'gameid', 'title', 'faixa_preco',
                    'genre_list', 'release_date', 'periodo'
                ]
                features_df = df_eval.drop(columns=[col for col in cols_to_drop if col in df_eval.columns])
                
                features_encoded = pd.get_dummies(features_df)
                
                # CORREÇÃO: Usar 'colunas_classificacao'
                X_pred = features_encoded.reindex(columns=colunas_classificacao, fill_value=0)

                # CORREÇÃO: Usar 'modelo_classificacao'
                y_pred = modelo_classificacao.predict(X_pred)
                accuracy = accuracy_score(y_true, y_pred)
                
                st.metric(label="Acurácia nos Dados Filtrados", value=f"{accuracy:.2%}")

                if y_true.nunique() > 1:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    cm = confusion_matrix(y_true, y_pred, labels=labels)
                    sns.heatmap(cm, annot=True, fmt='g', ax=ax, cmap='Blues', xticklabels=labels, yticklabels=labels)
                    ax.set_xlabel('Previsto')
                    ax.set_ylabel('Verdadeiro')
                    ax.set_title('Matriz de Confusão')
                    st.pyplot(fig)
                else:
                    st.warning("Apenas uma classe presente nos dados filtrados. Não é possível gerar a Matriz de Confusão.")
    else:
        st.warning("Falha ao carregar o modelo/colunas de CLASSIFICAÇÃO ou não há dados filtrados para avaliação.")

# --- TAB DE PREDIÇÃO DE FAIXA DE PREÇO (CLASSIFICAÇÃO) ---
with tab_predicao:
    st.header("🚀 Predição de Faixa de Preço (Classificação)")
    st.markdown("Preencha as características abaixo para que o modelo classifique o jogo como 'Barato', 'Médio' ou 'Caro'.")
    st.markdown("---")

    if modelo_classificacao is not None and colunas_classificacao is not None:
        # --- Widgets de Entrada ---
        top_15_devs = sorted(dev_popularity.nlargest(15).index.tolist())
        top_15_pubs = sorted(pub_popularity.nlargest(15).index.tolist())
        plat_options = sorted(df_main['platform'].unique())
        
        col1, col2 = st.columns(2)
        with col1:
            class_dev = st.selectbox("Desenvolvedor (Top 15)", options=top_15_devs, key="class_dev")
            class_pub = st.selectbox("Publicadora (Top 15)", options=top_15_pubs, key="class_pub")
        with col2:
            class_plat = st.selectbox("Plataforma", options=plat_options, key="class_plat")
            class_year = st.number_input("Ano de Lançamento", min_value=1990, max_value=2025, value=2023, key="class_year")

        class_genres = st.multiselect("Selecione os Gêneros", options=all_genres_list, default=[all_genres_list[0]], key="class_genres")

        if st.button("Classificar Jogo", type="primary"):
            # 1. Criar um DataFrame de uma linha com os dados do usuário
            input_data = {
                'release_year': class_year,
                'platform': class_plat,
                'developers': class_dev,
                'publishers': class_pub
            }
            # 2. Adicionar as features de GÊNERO exatamente como no treino
            # Pega todas as colunas de gênero originais do dataframe principal
            all_original_genre_cols = [col for col in df_main.columns if col.startswith('genre_') and col != 'genre_list']
            for genre_col in all_original_genre_cols:
                # Extrai o nome do gênero (ex: 'Action' de 'genre_Action')
                genre_name = genre_col.replace('genre_', '')
                # Adiciona a coluna com valor 1 se o gênero foi selecionado, senão 0
                input_data[genre_col] = 1 if genre_name in class_genres else 0
            
            input_df = pd.DataFrame([input_data])

            # Define explicitamente quais colunas devem ser transformadas
            cols_to_encode = ['platform', 'developers', 'publishers']
            # O get_dummies agora manterá as colunas numéricas (release_year, genre_*)
            input_encoded = pd.get_dummies(input_df, columns=cols_to_encode)
            final_input = input_encoded.reindex(columns=colunas_classificacao, fill_value=0)
            
            # 3. Fazer a predição
            prediction = modelo_classificacao.predict(final_input)
            resultado = prediction[0]

            st.success(f"### O modelo classificou este jogo como: **{resultado}**")
            
    else:
        st.error("O modelo de classificação e/ou suas colunas não foram carregados. Verifique os logs na barra lateral.")


# --- TAB DE PREDIÇÃO DE PREÇO (REGRESSÃO) ---
with tab_pred_avancada:
    st.header("🤖 Previsão de Preço (Regressão)")
    st.markdown("Utilize o modelo de regressão para estimar o preço de um jogo com base em suas características, incluindo tendências de tempo e popularidade.")
    st.markdown("---")

    if modelo_regressao is not None and colunas_regressao is not None:

        # --- Widgets de Entrada ---
        top_50_devs = sorted(dev_popularity.nlargest(50).index.tolist())
        top_50_pubs = sorted(pub_popularity.nlargest(50).index.tolist())
        plat_options_advanced = sorted(df_main['platform'].unique())
        
        col1, col2 = st.columns(2)
        with col1:
            adv_dev = st.selectbox("Desenvolvedor (Top 50)", options=top_50_devs, key="adv_dev")
            adv_pub = st.selectbox("Publicadora (Top 50)", options=top_50_pubs, key="adv_pub")
            adv_plat = st.selectbox("Plataforma", options=plat_options_advanced, key="adv_plat")
        with col2:
            adv_future_date = st.date_input("Data de Lançamento", value=pd.to_datetime("2025-09-01"), key="adv_date")
            adv_genres = st.multiselect("Selecione os Gêneros", options=all_genres_list, default=[all_genres_list[0]], key="adv_genres")

        if st.button("Prever Preço", type="primary"):
            # 1. Preparar o DataFrame de Entrada com todas as features
            future_date_dt = pd.to_datetime(adv_future_date)
            input_data = {
                'platform': adv_plat,
                'developers': adv_dev,
                'publishers': adv_pub,
                'release_year': future_date_dt.year,
                'release_month': future_date_dt.month,
                'time_idx': (future_date_dt - df_main['release_date'].min()).days,
                'dev_popularity': dev_popularity.get(adv_dev, 0),
                'pub_popularity': pub_popularity.get(adv_pub, 0)
            }
            # 2. Adicionar as features de GÊNERO exatamente como no treino
            all_original_genre_cols = [col for col in df_main.columns if col.startswith('genre_') and col != 'genre_list']
            for genre_col in all_original_genre_cols:
                genre_name = genre_col.replace('genre_', '')
                input_data[genre_col] = 1 if genre_name in adv_genres else 0
            
            input_df = pd.DataFrame([input_data])

            # Define explicitamente quais colunas devem ser transformadas
            cols_to_encode = ['platform', 'developers', 'publishers']
            # O get_dummies agora manterá todas as outras colunas numéricas
            input_encoded = pd.get_dummies(input_df, columns=cols_to_encode)
            final_input = input_encoded.reindex(columns=colunas_regressao, fill_value=0)
            
            # 3. Fazer a Predição
            preco_previsto = modelo_regressao.predict(final_input)
            preco_usd = preco_previsto[0]

            # 4. Obter cotação atual do dólar
            cotacao = obter_cotacao_dolar()

            if cotacao:
                preco_brl = preco_usd * cotacao

                # 5. Exibir os Resultados
                st.success(f"### Previsão de Preço: **${preco_usd:.2f} USD    {preco_brl:.2f} BRL**")
                
                # O restante do código para exibir a métrica continua aqui...
                avg_price_platform = df_main[df_main['platform'] == adv_plat]['preco_dolar'].mean()
                avg_price_brl = avg_price_platform * cotacao
                st.metric(label=f"Preço Médio Atual para '{adv_plat}'", value=f"${avg_price_platform:.2f} USD", delta=f"R$ {avg_price_brl:.2f} BRL")
            else:
                # Se a cotação falhar, mostra apenas o valor em dólar
                st.success(f"### Previsão de Preço: **${preco_usd:.2f} USD**")
                st.warning("Não foi possível converter o valor para BRL no momento.")

            st.sidebar.markdown("---")
            st.sidebar.info(
    "Este dashboard interativo permite explorar dados de jogos, incluindo tendências de lançamento, "
    "preferências de gênero, atividades de desenvolvedores e distribuição de preços."
)