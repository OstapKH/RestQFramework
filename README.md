# Experiment Energy Consumption Visualizer

A Python-based visualization tool for monitoring and analyzing energy consumption metrics from experiments.

## Overview

This application visualizes energy consumption data for API servers (Java processes) and database servers (PostgreSQL processes) during benchmark experiments. It allows you to:

- Load experiment data from JSON files
- View detailed experiment configuration and results
- Visualize energy consumption patterns during experiment timeframes
- Compare energy usage between API and DB servers
- Analyze latency and throughput metrics

## Features

- **Filter by experiment**: Select specific experiments to analyze
- **Multiple visualization modes**:
  - Energy view: Basic energy consumption over time
  - Energy Comparative: Compare API and DB server energy usage side-by-side
  - Latency: View request latency distribution
  - Throughput: Compare throughput between runs
- **Plot types**: Line, Bar, and Scatter plots
- **Accumulation modes**: Simple (raw data) and Accumulated (cumulative energy usage)
- **Time-based filtering**: Automatically focuses on experiment timeframes
- **Interactive plots**: Pan, zoom, and save plots

## Requirements

- Python 3.6+
- Dependencies (see requirements.txt):
  - matplotlib
  - pandas
  - numpy
  - tkinter
  - pytz

## Installation

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the visualizer:
   ```
   python run_visualizer.py
   ```
   
2. Load a JSON data file using the "Load Data" button or File menu

3. Select an experiment from the dropdown menu

4. Choose visualization options:
   - Data Source: Energy, Energy Comparative, Latency, or Throughput
   - Plot Type: Line, Bar, or Scatter
   - Accumulation Mode: Simple or Accumulated (for energy data)
   - Window Size: Aggregation window in milliseconds

5. Use the plot toolbar to zoom, pan, or save the visualization

## Data Format

The application expects JSON files containing:
- `api_server_energy`: Array of energy measurements for API server
- `db_server_energy`: Array of energy measurements for DB server
- `benchmark_results`: Object containing experiment configurations and run results

## Notes

- Only Java processes are considered for API server energy
- Only PostgreSQL processes are considered for DB server energy
- "scaphandre" processes are automatically filtered out
- Energy data is filtered to match experiment timeframes 