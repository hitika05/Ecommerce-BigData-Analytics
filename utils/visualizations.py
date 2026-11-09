import plotly.express as px
import plotly.graph_objects as go

COLORS = ["#6750A4", "#2F80ED", "#16A085", "#F2994A", "#EB5757", "#14213D"]


def apply_plotly_theme() -> None:
    px.defaults.template = "plotly_white"
    px.defaults.color_discrete_sequence = COLORS


def empty_chart(message: str = "No data available") -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(text=message, x=.5, y=.5, xref="paper", yref="paper", showarrow=False, font={"size": 16, "color": "#667085"})
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return figure
