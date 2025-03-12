#!/bin/bash

# CPU-intensive simulation script
# Usage: ./cpu_load.sh [duration_in_seconds] [load_percentage]

duration=${1:-60}  # Default: 60 seconds
load=${2:-80}      # Default: 80% CPU load

echo "Starting CPU load simulation for $duration seconds at approximately $load% load"
echo "Process ID: $$"

end_time=$(($(date +%s) + duration))

while [ $(date +%s) -lt $end_time ]; do
    # Create CPU load by calculating prime numbers
    for i in {1..1000}; do
        echo "scale=10; sqrt($i)" | bc > /dev/null
    done
    
    # Sleep to adjust load percentage
    sleep_time=$(echo "scale=4; (100-$load)/100" | bc)
    sleep $sleep_time
done

echo "Simulation completed" 