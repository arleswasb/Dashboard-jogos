# 🎮 Dashboard de Análise de Jogos

Um dashboard interativo desenvolvido com Streamlit para análise de dados de jogos, incluindo tendências de lançamento, preferências de gênero, análise de desenvolvedores e distribuição de preços.

## 📋 Descrição do Projeto

Este projeto apresenta um dashboard web interativo que permite explorar e analisar dados abrangentes sobre a indústria de jogos. O dashboard oferece visualizações dinâmicas e filtros avançados para investigar tendências de mercado, padrões de lançamento e comportamento de preços ao longo do tempo.

### 🚀 Principais Funcionalidades

O dashboard está organizado em 7 abas principais:

1. **Visão Geral de Lançamentos e Gêneros**
   - Jogos lançados por ano
   - Top 10 gêneros por número de lançamentos
   - Distribuição de preços por gênero

2. **Análise por Plataforma e Desenvolvedor**
   - Lançamentos por plataforma ao longo do tempo
   - Top 10 desenvolvedores por número de lançamentos

3. **Distribuição de Preços e Tendências**
   - Análise detalhada da distribuição de preços
   - Tendências de preços por período

4. **Tendências de Lançamento por Período**
   - Análise comparativa entre períodos pré-pandemia, pandemia e pós-pandemia
   - Impacto dos eventos globais na indústria de jogos

5. **Visão Hierárquica**
   - Visualizações hierárquicas dos dados
   - Relações entre diferentes categorias

6. **Heatmap de Preços**
   - Mapa de calor mostrando preços médios por gênero e ano
   - Identificação de padrões temporais nos preços

7. **Informações Adicionais**
   - Documentação do projeto
   - Informações sobre fontes de dados

### 🎛️ Filtros Globais

O dashboard oferece filtros interativos que se aplicam a todas as visualizações:

- **Plataforma**: Filtragem por plataforma específica ou todas
- **Gênero**: Seleção múltipla de gêneros de jogos
- **Período da Pandemia**: Análise por períodos (Pré-Pandemia, Pandemia, Pós-Pandemia)
- **Intervalo de Anos**: Slider para selecionar período temporal específico

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **Streamlit** - Framework para criação do dashboard web
- **Pandas** - Manipulação e análise de dados
- **Plotly** - Visualizações interativas
- **NumPy** - Computação numérica
- **Matplotlib & Seaborn** - Visualizações complementares
- **Scikit-learn** - Processamento de dados de machine learning
- **Joblib** - Serialização de modelos

## 📁 Estrutura do Projeto

```
Dashboard-jogos/
├── dashboard_jogos_streamlit_v11a.py  # Arquivo principal do dashboard
├── DB_completo.csv                    # Dataset principal
├── requirements.txt                   # Dependências do projeto
├── README.md                         # Este arquivo
├── Background_app.jpg                # Imagem de fundo da aplicação
├── background_sidebar.jpg            # Imagem de fundo da sidebar
├── ufrn.png                         # Logo da UFRN
├── dca.png                          # Logo do DCA
├── modelo_classificacao_jogos.joblib # Modelo de classificação
├── modelo_regressao_preco.joblib     # Modelo de regressão de preços
├── colunas_classificacao_jogos.joblib # Colunas para classificação
└── colunas_regressao_preco.joblib    # Colunas para regressão
```

## ⚙️ Pré-requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

## 🚀 Como Executar o Projeto

### 1. Clone o Repositório

```powershell
git clone https://github.com/arleswasb/Dashboard-jogos.git
cd Dashboard-jogos
```

### 2. Instale as Dependências

```powershell
pip install -r requirements.txt
```

### 3. Execute o Dashboard

```powershell
streamlit run dashboard_jogos_streamlit_v11a.py
```

### 4. Acesse o Dashboard

Após executar o comando acima, o Streamlit automaticamente abrirá o dashboard no seu navegador padrão. Caso isso não aconteça, acesse:

```
http://localhost:8501
```

## 📊 Dados

O projeto utiliza o arquivo `DB_completo.csv` que contém informações sobre:

- **Títulos dos jogos**
- **Plataformas** (Steam, Epic Games, etc.)
- **Desenvolvedores e Publishers**
- **Gêneros** (múltiplos por jogo)
- **Datas de lançamento**
- **Preços** (em dólares e euros)
- **Classificações por período** (pré-pandemia, pandemia, pós-pandemia)

## 🔧 Principais Recursos Técnicos

### Cache de Dados
O dashboard utiliza `@st.cache_data` para otimizar o carregamento e processamento dos dados, melhorando significativamente a performance.

### Processamento de Dados
- Limpeza automática de caracteres não-ASCII
- Tratamento de datas e períodos temporais
- Normalização de gêneros múltiplos por jogo
- Filtros dinâmicos com recálculo automático de intervalos

### Visualizações Interativas
- Gráficos de linha para tendências temporais
- Gráficos de barras para rankings e distribuições
- Box plots para análise estatística
- Heatmaps para correlações temporais
- Gráficos de área empilhada para comparações

## 🎯 Casos de Uso

Este dashboard é ideal para:

- **Analistas de mercado** interessados em tendências da indústria de jogos
- **Desenvolvedores** que querem entender padrões de lançamento
- **Pesquisadores** estudando o impacto de eventos globais na indústria
- **Investidores** analisando oportunidades no setor de games
- **Estudantes** aprendendo análise de dados e visualização

## 🔍 Solução de Problemas

### Erro: Arquivo CSV não encontrado
```
ERRO: O arquivo CSV ('DB_completo.csv') não encontrado.
```
**Solução**: Certifique-se de que o arquivo `DB_completo.csv` está na mesma pasta do script principal.

### Erro de dependências
**Solução**: Execute novamente a instalação das dependências:
```powershell
pip install -r requirements.txt --upgrade
```

### Problemas de performance
**Solução**: O dashboard utiliza cache. Se houver problemas de performance, limpe o cache do Streamlit:
```powershell
streamlit cache clear
```

## 👨‍💻 Desenvolvimento

**Desenvolvido por**:   werbert arles de souza barradas 
**Instituição**: UFRN - Universidade Federal do Rio Grande do Norte  
**Departamento**: DCA - Departamento de Computação e Automação  

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor, abra uma issue ou submeta um pull request.

---

*Para mais informações ou suporte, entre em contato através do GitHub.*
