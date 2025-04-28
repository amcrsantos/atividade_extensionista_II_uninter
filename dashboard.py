import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def read_csv(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path, sep=";", on_bad_lines="skip")
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {file_path}: {e}")
        return None


def prepare_data(df, columns, institution_column="Instituição", apply_diff=True):
    df = df[df[institution_column].str.contains("Guarda", case=False, na=False)].copy()
    df["Período"] = pd.to_datetime(df["Período"], format="%Y-%m")
    df = df.sort_values("Período")
    df["Ano"] = df["Período"].dt.year
    df = df[df["Ano"] == 2024].copy()
    df_result = df[["Período"] + columns].copy()
    if apply_diff:
        df_result[columns] = df_result[columns].diff().fillna(df_result[columns])
    df_result["Mes_Ano"] = df_result["Período"].dt.month.map(
        {
            1: "Jan",
            2: "Fev",
            3: "Mar",
            4: "Abr",
            5: "Mai",
            6: "Jun",
            7: "Jul",
            8: "Ago",
            9: "Set",
            10: "Out",
            11: "Nov",
            12: "Dez",
        }
    )
    return df_result


def apply_filter(df, selected_months):
    df = df[df["Mes_Ano"].isin(selected_months)]
    return df


# Set columns to be used
col_manchester_protocol = [
    "Nº Atendimentos em Urgência SU Triagem Manchester -Vermelha",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Laranja",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Amarela",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Verde",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Azul",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Branca",
    "Nº Atendimentos s\ Triagem Manchester",
]
colors_manchester_protocol = {
    "Nº Atendimentos em Urgência SU Triagem Manchester -Vermelha": "red",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Laranja": "orange",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Amarela": "yellow",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Verde": "green",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Azul": "blue",
    "Nº Atendimentos em Urgência SU Triagem Manchester -Branca": "white",
    "Nº Atendimentos s\ Triagem Manchester": "purple",
}
col_medical_emergency_type = [
    "Urgências Geral",
    "Urgências Pediátricas",
    "Urgência Obstetricia",
    "Urgência Psiquiátrica",
]
col_medical_consultations = ["Nº Primeiras Consultas", "Nº Consultas Subsequentes"]
col_surgeries = [
    "Nº Intervenções Cirúrgicas Programadas",
    "Nº Intervenções Cirúrgicas Convencionais",
    "Nº Intervenções Cirúrgicas de Ambulatório",
    "Nº Intervenções Cirúrgicas Urgentes",
]
col_childbirths = ["Nº Total de Partos", "Nº Cesarianas"]
col_birth_projects = ["Nº Notícias Nascimento", "Nº de Nascer Utente"]
col_deaths = [
    "Óbitos",
    "Internamentos",
    "Descrição Capítulo Diagnóstico Principal",
    "Sexo",
    "Faixa Etária",
]

# Load and prepare data
manchester_protocol = prepare_data(
    read_csv("./files/atendimentos-em-urgencia-triagem-manchester.csv"),
    col_manchester_protocol,
)
medical_emergency_type = prepare_data(
    read_csv("./files/atendimentos-por-tipo-de-urgencia-hospitalar.csv"),
    col_medical_emergency_type,
)
medical_consultations = prepare_data(
    read_csv("./files/evolucao-mensal-das-consultas-medicas-hospitalares.csv"),
    col_medical_consultations,
)
surgeries = prepare_data(read_csv("./files/intervencoes-cirurgicas.csv"), col_surgeries)
childbirths = prepare_data(read_csv("./files/partos-e-cesarianas.csv"), col_childbirths)
birth = prepare_data(
    read_csv(
        "./files/noticias-de-nascimento-digital-e-registo-de-nascer-de-utentes.csv"
    ),
    col_birth_projects,
    institution_column="Entidade",
    apply_diff=False,
)
deaths = prepare_data(
    read_csv("./files/morbilidade_mortalidade_hospit.csv"),
    col_deaths,
    institution_column="Instituição",
    apply_diff=False,
)


# Streamlit App
st.title("Dashboard - ULS Guarda 2024")

# Filtro de meses
available_months = manchester_protocol["Mes_Ano"].unique().tolist()
selected_months = st.multiselect(
    "Selecione os meses:", available_months, default=available_months
)

# Apply Filter
manchester_protocol = apply_filter(manchester_protocol, selected_months)
medical_emergency_type = apply_filter(medical_emergency_type, selected_months)
medical_consultations = apply_filter(medical_consultations, selected_months)
surgeries = apply_filter(surgeries, selected_months)
childbirths = apply_filter(childbirths, selected_months)
birth = apply_filter(birth, selected_months)
deaths = apply_filter(deaths, selected_months)

# Tabs
tabs = st.tabs(
    [
        "Triagem Manchester",
        "Tipos de Urgência",
        "Consultas Médicas",
        "Intervenções Cirúrgicas",
        "Morbilidade e Mortalidade",
        "Partos e Nascimentos",
    ]
)

with tabs[0]:
    st.markdown("### Evolução Mensal dos Atendimento em Urgência")
    fig = go.Figure()
    for col in col_manchester_protocol:
        fig.add_trace(
            go.Scatter(
                x=manchester_protocol["Mes_Ano"],
                y=manchester_protocol[col],
                mode="lines+markers",
                name=col,
                line=dict(color=colors_manchester_protocol.get(col, "black")),
            )
        )
    fig.update_layout(legend=dict(orientation="h", y=-0.4))
    st.plotly_chart(fig)

with tabs[1]:
    st.markdown("### Evolução Mensal dos Tipos de Urgência")
    fig = go.Figure()
    for col in col_medical_emergency_type:
        y_values = medical_emergency_type[col]
        if col == "Urgência Psiquiátrica":
            y_values = y_values.fillna(0)
        fig.add_trace(
            go.Scatter(
                x=medical_emergency_type["Mes_Ano"],
                y=y_values,
                mode="lines+markers",
                name=col,
            )
        )
    fig.update_layout(legend=dict(orientation="h", y=-0.4))
    st.plotly_chart(fig)

with tabs[2]:
    st.markdown("### Evolução Mensal das Consultas Médicas")
    fig = go.Figure()
    total_medical_consultations = (
        medical_consultations["Nº Primeiras Consultas"]
        + medical_consultations["Nº Consultas Subsequentes"]
    )
    percent_first_consultations = (
        medical_consultations["Nº Primeiras Consultas"] / total_medical_consultations
    ) * 100
    percent_subsequent_consultations = (
        medical_consultations["Nº Consultas Subsequentes"] / total_medical_consultations
    ) * 100

    fig.add_trace(
        go.Bar(
            x=medical_consultations["Mes_Ano"],
            y=percent_first_consultations,
            name="Primeiras Consultas",
        )
    )
    fig.add_trace(
        go.Bar(
            x=medical_consultations["Mes_Ano"],
            y=percent_subsequent_consultations,
            name="Consultas Subsequentes",
        )
    )
    fig.update_layout(
        barmode="stack",
        legend=dict(orientation="h", y=-0.4),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        hovermode="x unified",
        yaxis_title="Percentual (%)",
    )
    fig.update_traces(texttemplate="%{y:.1f}%", textposition="inside")
    st.plotly_chart(fig)

with tabs[3]:
    st.markdown("### Evolução Mensal das Intervenções Cirúrgicas")
    fig = go.Figure()
    for col in col_surgeries:
        fig.add_trace(
            go.Scatter(
                x=surgeries["Mes_Ano"], y=surgeries[col], mode="lines+markers", name=col
            )
        )
    fig.update_layout(legend=dict(orientation="h", y=-0.4))
    st.plotly_chart(fig)

with tabs[4]:
    total_deaths = deaths["Óbitos"].sum()
    st.metric(label="Total de Óbitos", value=int(total_deaths))

    st.markdown("---")
    st.markdown("### Internamentos, Óbitos e Taxa de Letalidade por Diagnóstico")
    data_diag = (
        deaths.groupby("Descrição Capítulo Diagnóstico Principal")
        .agg({"Internamentos": "sum", "Óbitos": "sum"})
        .reset_index()
    )
    data_diag["Taxa Letalidade (%)"] = (
        data_diag["Óbitos"] / data_diag["Internamentos"]
    ) * 100
    data_diag = data_diag.fillna(0)
    data_diag = data_diag.sort_values(by="Internamentos", ascending=False)

    fig_diag = go.Figure()
    fig_diag.add_trace(
        go.Bar(
            x=data_diag["Descrição Capítulo Diagnóstico Principal"],
            y=data_diag["Internamentos"],
            name="Internamentos",
        )
    )

    fig_diag.add_trace(
        go.Bar(
            x=data_diag["Descrição Capítulo Diagnóstico Principal"],
            y=data_diag["Óbitos"],
            name="Óbitos",
        )
    )

    fig_diag.add_trace(
        go.Scatter(
            x=data_diag["Descrição Capítulo Diagnóstico Principal"],
            y=data_diag["Taxa Letalidade (%)"],
            name="Taxa de Letalidade (%)",
            mode="lines+markers",
            yaxis="y2",
        )
    )

    fig_diag.update_layout(
        title="Internamentos, Óbitos e Taxa de Letalidade por Diagnóstico",
        xaxis_title="Diagnóstico",
        yaxis_title="Quantidade",
        yaxis2=dict(title="Taxa de Letalidade (%)", overlaying="y", side="right"),
        barmode="group",
        legend=dict(orientation="h", y=1.4, x=0.5, xanchor="center"),
        xaxis_tickangle=-60,
        xaxis=dict(tickfont=dict(size=10)),
        margin=dict(l=40, r=20, t=100, b=150),
        hovermode="x unified",
    )
    st.plotly_chart(fig_diag)

    st.markdown("---")
    st.subheader("Distribuição por Gênero e Faixa Etária - Selecionar Diagnóstico")
    unique_diagnostics = (
        deaths["Descrição Capítulo Diagnóstico Principal"].dropna().unique()
    )
    selected_diagnostics = st.selectbox(
        "Selecione um diagnóstico:", sorted(unique_diagnostics)
    )

    filtered_data = deaths[
        deaths["Descrição Capítulo Diagnóstico Principal"] == selected_diagnostics
    ]

    total_internamentos = filtered_data["Internamentos"].sum()
    total_deaths_diag = filtered_data["Óbitos"].sum()
    if total_internamentos > 0:
        taxa_letalidade = (total_deaths_diag / total_internamentos) * 100
    else:
        taxa_letalidade = 0

    st.metric(
        label=f"Taxa Média de Letalidade - {selected_diagnostics}",
        value=f"{taxa_letalidade:.2f}%",
    )

    st.markdown("---")
    st.markdown(f"### Distribuição por Gênero - {selected_diagnostics}")
    gender_internamentos = filtered_data.groupby("Sexo")["Internamentos"].sum()
    gender_deaths = filtered_data.groupby("Sexo")["Óbitos"].sum()

    fig_gender = go.Figure()
    fig_gender.add_trace(
        go.Bar(
            x=gender_internamentos.index,
            y=gender_internamentos.values,
            name="Internamentos",
            marker_color="#1f77b4",
        )
    )
    fig_gender.add_trace(
        go.Bar(
            x=gender_deaths.index,
            y=gender_deaths.values,
            name="Óbitos",
            marker_color="#d62728",
        )
    )

    fig_gender.update_layout(
        barmode="group",
        title="Distribuição de Internamentos e Óbitos por Gênero",
        xaxis_title="Gênero",
        yaxis_title="Quantidade",
        legend=dict(orientation="h", y=-0.4),
        hovermode="x unified",
        margin=dict(l=40, r=20, t=60, b=60),
    )
    st.plotly_chart(fig_gender)

    # Gráfico Distribuição por Faixa Etária
    st.markdown(f"### Distribuição por Faixa Etária - {selected_diagnostics}")

    ordem_range = [
        "[0-1[",
        "[1-5[",
        "[5-15[",
        "[15-25[",
        "[25-45[",
        "[45-65[",
        "[65-120[",
    ]

    filtered_data["Faixa Etária"] = pd.Categorical(
        filtered_data["Faixa Etária"], categories=ordem_range, ordered=True
    )

    range_internamentos = (
        filtered_data.groupby("Faixa Etária")["Internamentos"]
        .sum()
        .reindex(ordem_range)
    )
    range_deaths = (
        filtered_data.groupby("Faixa Etária")["Óbitos"].sum().reindex(ordem_range)
    )

    fig_range = go.Figure()
    fig_range.add_trace(
        go.Bar(
            y=range_internamentos.index,
            x=range_internamentos.values,
            name="Internamentos",
            orientation="h",
            marker_color="#1f77b4",
        )
    )
    fig_range.add_trace(
        go.Bar(
            y=range_deaths.index,
            x=range_deaths.values,
            name="Óbitos",
            orientation="h",
            marker_color="#d62728",
        )
    )

    fig_range.update_layout(
        barmode="group",
        title="Distribuição de Internamentos e Óbitos por Faixa Etária",
        xaxis_title="Quantidade",
        yaxis_title="Faixa Etária",
        legend=dict(orientation="h", y=-0.4),
        hovermode="y unified",
        margin=dict(l=80, r=20, t=60, b=60),
    )
    st.plotly_chart(fig_range)

with tabs[5]:
    st.markdown("### Evolução Mensal dos Partos e Cesarianas")
    fig_childbirths = go.Figure()

    # Usar os valores mensais diretamente
    total_childbirths = childbirths["Nº Total de Partos"]
    c_sections = childbirths["Nº Cesarianas"]
    childbirths_vaginal_birth = total_childbirths - c_sections

    percent_vaginal_birth = (childbirths_vaginal_birth / total_childbirths) * 100
    percent_c_sections = (c_sections / total_childbirths) * 100

    fig_childbirths.add_trace(
        go.Bar(
            x=childbirths["Mes_Ano"],
            y=percent_vaginal_birth,
            name="Partos Vaginais",
            customdata=childbirths_vaginal_birth,
            hovertemplate="%{x}<br>Percentual: %{y:.1f}%<br>Quantidade: %{customdata}<extra></extra>",
        )
    )
    fig_childbirths.add_trace(
        go.Bar(
            x=childbirths["Mes_Ano"],
            y=percent_c_sections,
            name="Cesarianas",
            customdata=c_sections,
            hovertemplate="%{x}<br>Percentual: %{y:.1f}%<br>Quantidade: %{customdata}<extra></extra>",
        )
    )
    fig_childbirths.update_layout(
        barmode="stack",
        legend=dict(orientation="h", y=-0.4),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        hovermode="x unified",
        yaxis_title="Percentual (%)",
    )
    fig_childbirths.update_traces(texttemplate="%{y:.1f}%", textposition="inside")
    st.plotly_chart(fig_childbirths)

    st.markdown("---")
    st.markdown("### Comparação Mensal: Notícias de Nascimento vs Nascer Utente")
    fig_birth_projects = go.Figure()

    fig_birth_projects.add_trace(
        go.Bar(
            x=birth["Mes_Ano"],
            y=birth["Nº Notícias Nascimento"],
            name="Notícias de Nascimento",
        )
    )
    fig_birth_projects.add_trace(
        go.Bar(
            x=birth["Mes_Ano"],
            y=birth["Nº de Nascer Utente"],
            name="Nascer Utente",
        )
    )
    fig_birth_projects.update_layout(
        barmode="group",
        legend=dict(orientation="h", y=-0.4),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        hovermode="x unified",
        yaxis_title="Quantidade",
    )
    st.plotly_chart(fig_birth_projects)
