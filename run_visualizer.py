#!/usr/bin/env python3
"""
Energy Consumption Experiment Visualizer
----------------------------------------
This script launches the Energy Consumption Visualizer for API and DB servers.
It provides visualization of energy usage during benchmark experiments.

Usage:
    python run_visualizer.py

Requirements:
    - Python 3.6+
    - tkinter
    - matplotlib
    - pandas
    - numpy
    - pytz
"""

from visualizer import ExperimentVisualizer
import tkinter as tk

if __name__ == "__main__":
    # Create the root window
    root = tk.Tk()
    # Set a specific icon and window title
    root.title("Experiment Energy Consumption Visualizer")
    
    try:
        # Try to set an icon if available (optional)
        root.iconbitmap("icon.ico")  # You can create and add an icon file if needed
    except:
        # Just continue if icon setting fails
        pass
    
    # Create the application instance
    app = ExperimentVisualizer(root)
    
    # Start the main event loop
    root.mainloop() 