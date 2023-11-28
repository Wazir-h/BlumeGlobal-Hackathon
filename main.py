

import numpy as np
import pandas as pd
import data_sieve
import pickle
import os
import sys
from functools import partial
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

filepath = './data.xlsx'
data_sieve.update_data(filepath)
tn = os.stat(filepath).st_mtime
bfile = open('warehouse_data.dat','rb')
warehouse_data = pickle.load(bfile)

if(tn > warehouse_data['time']):
  data_sieve.update_data(filepath)
  with open('warehouse_data.dat','rb') as file:
    warehouse_data = pickle.load(file)

bfile.close()

#Conventional : speed = 40 //scaled to 40/6
#EV : speed = 45 // scaled to 45/6
# time is scaled to t*6

def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data["distance_matrix"] = warehouse_data[1][0]
    data["num_vehicles"] = warehouse_data[1][1]+warehouse_data[1][2]
    data["demands"] = [0, 1, 1, 2, 4, 2, 4, 6]
    data["vehicle_capacities"] = [15, 15, 15, 15,15,10]
    data["depot"] = 0
    return data

def print_solution(manager, routing, solution):
    """Prints solution on console."""
    print(f'Objective: {solution.ObjectiveValue()}')
    max_route_time = 0
    for vehicle_id in range(manager.GetNumberOfVehicles()):
        index = routing.Start(vehicle_id)
        plan_output = f'Route for vehicle {vehicle_id}:\n'
        route_time = 0
        while not routing.IsEnd(index):
            plan_output += f'{manager.IndexToNode(index)} '
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            time = routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            plan_output += f'--{time}min--> '
            route_time += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        plan_output += f'{manager.IndexToNode(index)}\n'
        plan_output += f'Time of the route: {route_time}min\n'
        print(plan_output)
        max_route_time = max(route_time, max_route_time)
    print(f'Maximum of the route time: {max_route_time}min')

def print_solution_load(data, manager, routing, solution):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = f"Route for vehicle {vehicle_id}:\n"
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            plan_output += f" {node_index} Load({route_load}) -> "
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        plan_output += f" {manager.IndexToNode(index)} Load({route_load})\n"
        plan_output += f"Distance of the route: {route_distance}m\n"
        plan_output += f"Load of the route: {route_load}\n"
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print(f"Total distance of all routes: {total_distance}m")
    print(f"Total load of all routes: {total_load}")


data = create_data_model()

# Create the routing index manager.
manager = pywrapcp.RoutingIndexManager(
    len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
)

# Create Routing Model.
routing = pywrapcp.RoutingModel(manager)


# Create and register a transit callback.
def time_callback(from_index, to_index, speed):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data["distance_matrix"][from_node][to_node]*speed

slow_callback = partial(time_callback, speed=9)
fast_callback = partial(time_callback, speed=8)

slow_index = routing.RegisterTransitCallback(slow_callback)
fast_index = routing.RegisterTransitCallback(fast_callback)

# Define cost of each arc for each vehicle.
routing.SetArcCostEvaluatorOfVehicle(slow_index, 0)
routing.SetArcCostEvaluatorOfVehicle(slow_index, 1)
routing.SetArcCostEvaluatorOfVehicle(slow_index, 2)
routing.SetArcCostEvaluatorOfVehicle(slow_index, 3)
routing.SetArcCostEvaluatorOfVehicle(slow_index, 4)
routing.SetArcCostEvaluatorOfVehicle(fast_index, 5)

# Add Distance constraint.
dimension_name = 'Time'
routing.AddDimensionWithVehicleTransitAndCapacity(
    [slow_index, slow_index, slow_index, slow_index, slow_index, fast_index],
    0,  # no slack
    [3000*6, 3000*6, 3000*6, 3000*6, 3000*6, 490*6],  # vehicle maximum travel time
    True,  # start cumul to zero
    dimension_name)


def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,  # null capacity slack
    data["vehicle_capacities"],  # vehicle maximum capacities
    True,  # start cumul to zero
    "Capacity",
)
# Setting first solution heuristic.
search_params = pywrapcp.DefaultRoutingSearchParameters()
search_params.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

#search_params.log_search = True
search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
search_params.time_limit.seconds = 10

# Solve the problem.
solution = routing.SolveWithParameters(search_params)

# Print solution on console.

with open('routing.txt','w') as sys.stdout:
    print_solution(manager, routing, solution)
    print_solution_load(data, manager, routing, solution)


