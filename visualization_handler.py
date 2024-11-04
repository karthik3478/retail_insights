import plotly.express as px
import pandas as pd

class VisualizationHandler:
    def __init__(self):
        self.chart_types = {
            'bar': self.create_bar_chart,
            'line': self.create_line_chart,
            'pie': self.create_pie_chart
        }

    def create_visualization(self, df: pd.DataFrame, viz_config: dict):
        if viz_config['type'] == 'none':
            return None
            
        chart_func = self.chart_types.get(viz_config['type'])
        if not chart_func:
            return None
            
        return chart_func(df, viz_config)

    def create_bar_chart(self, df, config):
        fig = px.bar(
            df,
            x=config['x_axis'],
            y=config['y_axis'],
            title=config['title']
        )
        return fig

    def create_line_chart(self, df, config):
        fig = px.line(
            df,
            x=config['x_axis'],
            y=config['y_axis'],
            title=config['title']
        )
        return fig

    def create_pie_chart(self, df, config):
        fig = px.pie(
            df,
            values=config['y_axis'],
            names=config['x_axis'],
            title=config['title']
        )
        return fig 