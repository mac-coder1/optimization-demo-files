from itertools import cycle

import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def compile_tours(
    n_vehicles, routing, manager, solution, allow_arbitrary_end_locations
):
    """
    Extracts each vehicle's route from the solution and returns a list of tours.
    Also extracts the travel time between the nodes.

    Args:
        allow_arbitrary_end_locations:
            If True, the end location of the vehicle can be any node. To mimic this in the code the final
            node is made 0 distance from all others. So must be removed from the plot!

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
            if allow_arbitrary_end_locations:
                continue

            node_index = manager.IndexToNode(index)
            tours[-1].append(node_index)

    return tours


def plot_tours(tours, coordinates, dropped_nodes):
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

    t_dropped = np.array(dropped_nodes)
    x_dropped = coordinates.values[t_dropped, 0]
    y_dropped = coordinates.values[t_dropped, 1]

    # Add scatter plot for dropped nodes
    fig.add_trace(
        go.Scatter(
            x=x_dropped,
            y=y_dropped,
            mode="markers",
            marker=dict(color="black"),
            name="Dropped Apps",
        )
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


def print_solution(
    routing,
    n_vehicles,
    start_times,
    end_times,
    time_dimension,
    solution,
    manager,
    time_matrix,
    service_time_dict,
    dataset,
):
    """
    Description: Prints the solution of the VRP problem on an engineer by engineer basis.
    """

    cumulative_job_drive_time = 0
    cumulative_drive_time = 0
    cumulative_job_time = 0

    av_util = 0

    print_val = "Key: |Node| A:Arrival, JT:Job Time, T:Travel Time, J:Job Time, F:Finish Time, WT: Work Time\n\n"
    for vehicle_id in range(n_vehicles):
        print_val += f"Vehicle {vehicle_id}: Available {start_times[vehicle_id]}min -> {end_times[vehicle_id]}min\n"

        index = routing.Start(vehicle_id)
        previous_index = None

        total_job_drive_time = 0
        total_drive_time = 0
        total_job_time = 0

        while not routing.IsEnd(index):

            previous_index = index
            previous_node = manager.IndexToNode(index)

            index = solution.Value(routing.NextVar(index))
            node = manager.IndexToNode(index)

            # arrival_time = solution.Min(time_dimension.CumulVar(previous_node))
            arrival_time = solution.Min(time_dimension.CumulVar(previous_index))

            job_drive_time = routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )

            total_job_drive_time += job_drive_time

            drive_time = time_matrix[previous_node][node]

            total_drive_time += drive_time

            job_time = service_time_dict[dataset.loc[previous_node, "job_type"]]

            total_job_time += job_time

            print_val += f"|{previous_node}| A:{arrival_time}, TS: {dataset.loc[previous_node, 'timeslot']}, JT:{job_drive_time}, T:{drive_time}, J:{job_time} -> "

        index = routing.End(vehicle_id)
        print_val += f"F:{solution.Value(time_dimension.CumulVar(index))} min\n"

        print_val += f"Totals: J:{total_job_time},    T:{total_drive_time}, JT:{total_job_drive_time}, F:{solution.Value(time_dimension.CumulVar(index))} min\n"
        WT_total = (end_times[vehicle_id] - start_times[vehicle_id]) / 100
        av_util += (total_job_time) / WT_total
        print_val += f"Percentages: J:{int(total_job_time/WT_total)}%,    T:{int(total_drive_time/WT_total)}%, JT:{int(total_job_drive_time/WT_total)}%, F:%{int(solution.Value(time_dimension.CumulVar(index))/WT_total)}%\n\n"

        cumulative_job_drive_time += total_job_drive_time
        cumulative_drive_time += total_drive_time
        cumulative_job_time += total_job_time

    print_val += f"Totals: J:{cumulative_job_time} T:{cumulative_drive_time}, JT:{cumulative_job_drive_time}\n"
    print_val += f"Average Utilisation: {round(av_util/n_vehicles,2)}%\n"

    print(print_val)

    print(f"Objective function value: {solution.ObjectiveValue()} min")

    print(f"Ob function directly minimises JT, not finish time")


def print_appointments(
    dataset,
    time_dimension,
    manager,
    solution,
    start_locations,
    time_window_dict,
    routing,
):
    """
    Desc: Prints the outputs of the VRP on a per appointment basis.
    """
    # find dropped nodes
    dropped_nodes = []
    for index in range(routing.Size()):
        if routing.IsStart(index) or routing.IsEnd(index):
            continue
        if solution.Value(routing.NextVar(index)) == index:
            dropped_nodes.append(manager.IndexToNode(index))

    print("Appointments:")
    print("Key: |Node| (timeslot): Att: Arrival Time")
    print(f"AM {time_window_dict['AM']} min, PM {time_window_dict['PM']} min\n")

    for location_indx in dataset.index:
        if location_indx == 0:
            continue
        elif location_indx in start_locations:
            continue

        timeslot = dataset.loc[location_indx, "timeslot"]
        time_var = time_dimension.CumulVar(manager.NodeToIndex(location_indx))

        if location_indx in dropped_nodes:
            print(f"|{location_indx}| ({timeslot}): Not Attended")
        else:
            print(f"|{location_indx}| ({timeslot}): Att {solution.Value(time_var)}")

    return dropped_nodes
