<h3>Algorithm Description</h3>

The vehicle routing problem is solved using the OR-Tools library by Google. The algorithm considers both distance and capacity constraints.
The program taken account of all the orders placed in a particular day and assembles all the demand into one demand array, directly from the excel sheet. Also capacities are taken from the vehicle data.


- Distance Constraint:
The algorithm uses a time_callback function to calculate the time required based on the indices and the inverse of speed (labeled as speed in the code). Since the OR-Tools library only accepts integer values, the speed inverse values are normalized. The time_callback method returns distance * speed, where speed is actually the speed inverse.

- Capacity Constraint:
A standard template is implemented to handle the capacity constraint. It uses a demand array for the nodes and a capacity array for the vehicles. The capacity for every drop location is taken and stored, and the algorithm implments the solution outputting the load each vehicle will carry for delivery.

Implementation:

The algorithm provides an optimal solution that satisfies both the distance and capacity constraints. The solution is then outputted to the routing.txt file.

