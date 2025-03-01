# Experiment Energy Consumption Visualizer

This tool visualizes energy consumption data from experiments for API and DB servers.

## Features

- Two-panel interface: experiment details on the left and energy consumption plots on the right
- Load and visualize JSON data files containing experiment results
- Select different experiments via dropdown menu
- Toggle between line charts and bar charts
- Scrollable experiment details view

## Requirements

To run this application, you need:

- Python 3.6 or higher
- tkinter (usually comes with Python)
- matplotlib
- pandas

## Installation

1. Ensure Python is installed on your system
2. Install required packages:

```bash
pip install matplotlib pandas
```

## Usage

1. Run the script:

```bash
python visualizer.py
```

2. Click "Load Data" to select a JSON file containing experiment data
3. Use the dropdown menu to switch between different experiments
4. View experiment details in the left panel
5. View energy consumption plots in the right panel
6. Toggle between "Line" and "Bar" chart types using the dropdown

## Data Format

The visualizer expects JSON data in one of the following formats:

### Option 1: Dictionary of experiments

```json
{
  "experiment_id_1": {
    "parameter1": "value1",
    "parameter2": "value2",
    "energy_consumption": {
      "api": [10, 20, 30, 40],
      "db": [5, 15, 25, 35]
    }
  },
  "experiment_id_2": {
    ...
  }
}
```

### Option 2: List of experiments

```json
[
  {
    "id": "experiment_id_1",
    "parameter1": "value1",
    "parameter2": "value2",
    "api_server": {
      "energy": [10, 20, 30, 40]
    },
    "db_server": {
      "energy": [5, 15, 25, 35]
    }
  },
  {
    "id": "experiment_id_2",
    ...
  }
]
```

## Customizing

You can modify the `visualizer.py` script to adapt it to your specific data structure if needed. Check the comments in the code for guidance on where to make changes. 