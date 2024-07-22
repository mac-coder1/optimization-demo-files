from itertools import cycle

import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def compile_tours(n_vehicles, routing, manager, solution):
    """
    Extracts each vehicle's route from the solution and returns a list of tours.
    """
    tours = []
    for vehicle_id in range(n_vehicles):
        index = routing.Start(vehicle_id)
        tours.append([])
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            tours[-1].append(node_index)
        else:
            node_index = manager.IndexToNode(index)
            tours[-1].append(node_index)

    return tours


def plot_tours(tours, coordinates):
    """
    Plots the graph of tours for each vehicle
    """
    # Colors cycle from Plotly's built-in color scale
    colors = cycle(px.colors.qualitative.Plotly)

    # Initialize Plotly figure
    fig = go.Figure()

    # Loop over the tours to add scatter and line plots
    for r, tour in enumerate(tours):
        c = next(colors)
        t = np.array(tour)
        x = coordinates.values[t, 0]
        y = coordinates.values[t, 1]

        # Add scatter plot
        fig.add_trace(
            go.Scatter(x=x, y=y, mode="markers", marker=dict(color=c), name=f"R{r}")
        )

        # Add line plot
        fig.add_trace(
            go.Scatter(x=x, y=y, mode="lines", line=dict(color=c), showlegend=False)
        )

    # Update layout to include legend and other layout adjustments
    fig.update_layout(
        title="Tours Visualization",
        xaxis_title="X Coordinates",
        yaxis_title="Y Coordinates",
        legend_title="Tours",
        legend=dict(
            x=1,
            y=1.02,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255, 255, 255, 0.5)",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    return fig
