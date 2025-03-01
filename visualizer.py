import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta, timezone
import pytz  # For timezone handling
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

class ExperimentVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Experiment Energy Consumption Visualizer")
        self.root.geometry("1200x800")
        self.data = None
        # Use EET timezone for display
        self.display_timezone = pytz.timezone('Europe/Kiev')  # East European Time
        
        # Set up main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a PanedWindow to divide the UI into left and right panels
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Experiment Details
        self.left_frame = ttk.Frame(self.paned_window, width=400)
        self.paned_window.add(self.left_frame, weight=1)
        
        # Right panel - Energy Consumption Plots
        self.right_frame = ttk.Frame(self.paned_window, width=800)
        self.paned_window.add(self.right_frame, weight=2)
        
        # Configure the left panel
        self.setup_left_panel()
        
        # Configure the right panel
        self.setup_right_panel()
        
        # File menu and controls
        self.setup_menu()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Please load a data file.")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_menu(self):
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Load Data", command=self.load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Reset Plot View", command=self.reset_plot_view)
        menu_bar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menu_bar)
        
        # Add a frame for controls at the top
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 15))
        
        # Create a more visible Load Data button with increased size and padding
        load_button = ttk.Button(control_frame, text="Load Data", command=self.load_data)
        load_button.pack(side=tk.LEFT, padx=10, pady=5)
        # Apply style to make button larger and more visible
        style = ttk.Style()
        style.configure('Big.TButton', font=('Arial', 11, 'bold'))
        load_button.configure(style='Big.TButton')
    
    def reset_plot_view(self):
        """Reset the plot view to default - Placeholder for future implementation"""
        self.status_var.set("Plot view reset functionality will be implemented in the future")
    
    def setup_left_panel(self):
        # Title
        ttk.Label(self.left_frame, text="Experiment Details", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Create a frame for experiment selector
        selector_frame = ttk.Frame(self.left_frame)
        selector_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(selector_frame, text="Select Experiment:").pack(side=tk.LEFT, padx=5)
        self.experiment_var = tk.StringVar()
        self.experiment_selector = ttk.Combobox(selector_frame, textvariable=self.experiment_var, state="readonly")
        self.experiment_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Bind to ComboboxSelected event - ensure it triggers plot update
        self.experiment_selector.bind("<<ComboboxSelected>>", self.on_experiment_selected)
        
        # Add a refresh button to force plot update
        ttk.Button(selector_frame, text="Refresh Plot", command=self.force_plot_update).pack(side=tk.RIGHT, padx=5)
        
        # Scrollable frame for details
        frame_canvas = ttk.Frame(self.left_frame)
        frame_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a canvas with scrollbar
        canvas = tk.Canvas(frame_canvas)
        scrollbar = ttk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        self.details_frame = ttk.Frame(canvas)
        
        # Configure scrollbar and canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create window in canvas for details_frame
        canvas_frame = canvas.create_window((0, 0), window=self.details_frame, anchor="nw")
        
        # Update scrollregion when frame size changes
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"), width=350)
        
        self.details_frame.bind("<Configure>", configure_canvas)
        
        # Make canvas expand with window
        def configure_canvas_frame(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_frame)
    
    def setup_right_panel(self):
        # Title
        ttk.Label(self.right_frame, text="Energy Consumption", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Frame for the plot
        self.plot_frame = ttk.Frame(self.right_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the matplotlib figure and canvas
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add matplotlib toolbar for zoom, pan, save, etc.
        toolbar_frame = ttk.Frame(self.plot_frame)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Add plot control buttons
        control_frame = ttk.Frame(self.right_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Refresh Plot", command=self.force_plot_update).pack(side=tk.LEFT, padx=5)
        
        # Plot type selection
        ttk.Label(control_frame, text="Plot Type:").pack(side=tk.LEFT, padx=5)
        self.plot_type_var = tk.StringVar(value="Line")
        plot_type_combo = ttk.Combobox(control_frame, textvariable=self.plot_type_var, 
                                      values=["Line", "Bar", "Scatter"], state="readonly", width=10)
        plot_type_combo.pack(side=tk.LEFT, padx=5)
        # Update callback to use force_plot_update for more reliable refresh
        plot_type_combo.bind("<<ComboboxSelected>>", lambda e: self.force_plot_update())
        
        # Plot data selection
        ttk.Label(control_frame, text="Data Source:").pack(side=tk.LEFT, padx=5)
        self.data_source_var = tk.StringVar(value="Energy")
        data_source_combo = ttk.Combobox(control_frame, textvariable=self.data_source_var, 
                                      values=["Energy", "Energy Comparative", "Latency", "Throughput"], state="readonly", width=14)
        data_source_combo.pack(side=tk.LEFT, padx=5)
        # Update callback to use force_plot_update for more reliable refresh
        data_source_combo.bind("<<ComboboxSelected>>", lambda e: self.force_plot_update())
        
        # Accumulation mode selection (for energy comparative)
        ttk.Label(control_frame, text="Accumulation:").pack(side=tk.LEFT, padx=5)
        self.accumulation_var = tk.StringVar(value="Simple")
        accumulation_combo = ttk.Combobox(control_frame, textvariable=self.accumulation_var, 
                                      values=["Simple", "Accumulated"], state="readonly", width=10)
        accumulation_combo.pack(side=tk.LEFT, padx=5)
        # Update callback to use force_plot_update for more reliable refresh
        accumulation_combo.bind("<<ComboboxSelected>>", lambda e: self.force_plot_update())
        
        # Window size for accumulation (ms)
        ttk.Label(control_frame, text="Window Size (ms):").pack(side=tk.LEFT, padx=5)
        self.window_size_var = tk.StringVar(value="100")
        window_size_entry = ttk.Entry(control_frame, textvariable=self.window_size_var, width=6)
        window_size_entry.pack(side=tk.LEFT, padx=5)
        # Update callback to use force_plot_update for more reliable refresh
        window_size_entry.bind("<Return>", lambda e: self.force_plot_update())
        
        # Add help tooltip about navigation
        ttk.Label(control_frame, text="Plot visualization will be implemented in future versions", 
                 font=("Arial", 8, "italic")).pack(side=tk.RIGHT, padx=10)
    
    def load_data(self):
        file_path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.status_var.set(f"Loading data from {os.path.basename(file_path)}...")
            self.root.update_idletasks()
            
            with open(file_path, 'r') as file:
                self.data = json.load(file)
            
            # Check if the data has the expected structure
            if not all(key in self.data for key in ["api_server_energy", "db_server_energy", "benchmark_results"]):
                messagebox.showerror("Error", "The file does not have the expected structure.")
                return
                
            # Extract experiment names from benchmark_results.experiments
            if "benchmark_results" in self.data and "experiments" in self.data["benchmark_results"]:
                experiment_ids = list(self.data["benchmark_results"]["experiments"].keys())
                self.experiment_selector['values'] = experiment_ids
                if experiment_ids:
                    self.experiment_selector.current(0)
                    # Force selection of first experiment and update plot after loading data
                    self.experiment_var.set(experiment_ids[0])
                    self.on_experiment_selected(None)
                self.status_var.set(f"Loaded {len(experiment_ids)} experiments from {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "No experiments found in the data file.")
                self.status_var.set("No experiments found in the data file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_var.set("Error loading data file")
    
    def on_experiment_selected(self, event):
        if not self.data or not self.experiment_var.get():
            return
            
        # Debug message to confirm selection change
        selected_experiment = self.experiment_var.get()
        self.status_var.set(f"Selected experiment: {selected_experiment} - Updating display...")
        self.root.update_idletasks()  # Force UI update
        
        # Clear previous details
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        # Get selected experiment data
        experiment_id = self.experiment_var.get()
        
        if "benchmark_results" in self.data and "experiments" in self.data["benchmark_results"]:
            experiment = self.data["benchmark_results"]["experiments"].get(experiment_id, {})
        else:
            return
        
        # Display experiment details
        row = 0
        ttk.Label(self.details_frame, text="Experiment Configuration", font=("Arial", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Display basic experiment configuration
        for key, value in experiment.items():
            if key != "runs" and not isinstance(value, (dict, list)):
                ttk.Label(self.details_frame, text=f"{key}:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                ttk.Label(self.details_frame, text=str(value), wraplength=250).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                row += 1
        
        # Display probabilities if they exist
        if "probabilities" in experiment:
            row += 1
            ttk.Label(self.details_frame, text="Endpoint Probabilities:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
            row += 1
            
            for endpoint, prob in experiment["probabilities"].items():
                ttk.Label(self.details_frame, text=f"  {endpoint}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                ttk.Label(self.details_frame, text=f"{prob * 100:.1f}%").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                row += 1
        
        # Show run summary if runs exist
        if "runs" in experiment and experiment["runs"]:
            row += 1
            ttk.Label(self.details_frame, text="Run Summary:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
            row += 1
            
            for i, run in enumerate(experiment["runs"]):
                ttk.Label(self.details_frame, text=f"Run {i+1}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                
                # Show start time in human readable format with EET timezone
                if "start_timestamp" in run:
                    # Convert milliseconds UTC to datetime with EET timezone
                    utc_dt = datetime.fromtimestamp(run["start_timestamp"]/1000, tz=timezone.utc)
                    eet_dt = utc_dt.astimezone(self.display_timezone)
                    ttk.Label(self.details_frame, text=f"Started: {eet_dt.strftime('%Y-%m-%d %H:%M:%S')} (EET)").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    row += 1
                
                if "successful_requests" in run and "total_requests" in run:
                    success_rate = (run["successful_requests"] / run["total_requests"]) * 100 if run["total_requests"] > 0 else 0
                    ttk.Label(self.details_frame, text=f"{success_rate:.1f}% success ({run['successful_requests']}/{run['total_requests']})").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                elif "throughput" in run:
                    ttk.Label(self.details_frame, text=f"Throughput: {run['throughput']:.2f} req/s").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                
                row += 1
                
                if "latency_distribution" in run:
                    ttk.Label(self.details_frame, text="  Latency (ms):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    latency_info = run["latency_distribution"]
                    median = latency_info.get("median_latency_ns", 0) / 1_000_000  # Convert ns to ms
                    p95 = latency_info.get("percentiles", {}).get("p95", 0) / 1_000_000
                    p99 = latency_info.get("percentiles", {}).get("p99", 0) / 1_000_000
                    ttk.Label(self.details_frame, text=f"Median: {median:.2f}, P95: {p95:.2f}, P99: {p99:.2f}").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    row += 1
        
        # Update the plot placeholder for this experiment
        self.update_plot()
        
        # Update status after plot is updated
        self.status_var.set(f"Displaying data for experiment: {selected_experiment}")
    
    def update_plot(self):
        """Update the plot with selected experiment data"""
        if not self.data or not self.experiment_var.get():
            return
        
        experiment_id = self.experiment_var.get()
        self.status_var.set(f"Updating plot for experiment: {experiment_id}")
        self.root.update_idletasks()  # Force UI update
        
        # Get the experiment time boundaries
        start_time_ms, end_time_ms = self.get_experiment_time_boundaries(experiment_id)
        
        # Debug info - show time boundaries in human-readable format
        if start_time_ms is not None and end_time_ms is not None:
            start_time_eet = self._convert_to_eet(start_time_ms).strftime('%Y-%m-%d %H:%M:%S')
            end_time_eet = self._convert_to_eet(end_time_ms).strftime('%Y-%m-%d %H:%M:%S')
            self.status_var.set(f"Experiment time bounds: {start_time_eet} to {end_time_eet} (EET)")
            self.root.update_idletasks()
        
        # Filter energy data to only include entries within the experiment time range
        api_energy_data = self.data.get("api_server_energy", [])
        db_energy_data = self.data.get("db_server_energy", [])
        
        filtered_api_data = self._filter_energy_data_by_time(api_energy_data, start_time_ms, end_time_ms)
        filtered_db_data = self._filter_energy_data_by_time(db_energy_data, start_time_ms, end_time_ms)
        
        # Clear the figure
        self.fig.clear()
        
        # Get the selected plot type and data source
        plot_type = self.plot_type_var.get()
        data_source = self.data_source_var.get()
        accumulation_mode = self.accumulation_var.get()
        
        try:
            window_size_ms = int(self.window_size_var.get())
        except ValueError:
            window_size_ms = 100  # Default if parsing fails
        
        # Process the energy data
        if data_source == "Energy":
            # Process API server data (java processes)
            api_df = self._process_energy_data(filtered_api_data, "java", window_size_ms)
            
            # Process DB server data (postgres processes)
            db_df = self._process_energy_data(filtered_db_data, "postgres", window_size_ms)
            
            # Create a new subplot
            ax = self.fig.add_subplot(111)
            
            # Configure the axis
            ax.set_xlabel('Time (EET)', fontsize=10)
            ax.set_ylabel('Energy Consumption', fontsize=10)
            ax.set_title(f'Energy Consumption for Experiment: {experiment_id}', fontsize=12)
            
            # Format the time axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S', tz=self.display_timezone))
            ax.tick_params(axis='x', rotation=45)
            
            # If either dataframe is empty, show a message
            if api_df.empty and db_df.empty:
                self.status_var.set("No energy data available for the selected time period")
                ax.text(0.5, 0.5, "No energy data available", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
            else:
                # Plot the data based on the selected plot type
                if plot_type == "Line":
                    if not api_df.empty:
                        ax.plot(api_df['datetime'], api_df['consumption'], 
                               label='API Server (Java)', color='red', linewidth=2, marker=None)
                    
                    if not db_df.empty:
                        ax.plot(db_df['datetime'], db_df['consumption'], 
                               label='DB Server (Postgres)', color='blue', linewidth=2, marker=None)
                
                elif plot_type == "Bar":
                    # For bar plots, we'll use bar width based on data density
                    bar_width = 0.0002  # Adjust as needed for visibility
                    
                    if not api_df.empty:
                        ax.bar(api_df['datetime'], api_df['consumption'], 
                              width=bar_width, label='API Server (Java)', color='blue', alpha=0.7)
                    
                    if not db_df.empty:
                        ax.bar(db_df['datetime'], db_df['consumption'], 
                              width=bar_width, label='DB Server (Postgres)', color='green', alpha=0.7)
                
                elif plot_type == "Scatter":
                    if not api_df.empty:
                        ax.scatter(api_df['datetime'], api_df['consumption'], 
                                 label='API Server (Java)', color='blue', marker='o', s=30)
                    
                    if not db_df.empty:
                        ax.scatter(db_df['datetime'], db_df['consumption'], 
                                 label='DB Server (Postgres)', color='green', marker='s', s=30)
                
                # Add legend
                ax.legend(loc='best')
                
                # Adjust the layout to fit the plot
                self.fig.tight_layout()
                
                # Show grid
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Use scientific notation for y-axis if values are large
                if not api_df.empty and api_df['consumption'].max() > 10000 or \
                   not db_df.empty and db_df['consumption'].max() > 10000:
                    ax.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
                
                # Update status with data summary
                api_count = len(api_df) if not api_df.empty else 0
                db_count = len(db_df) if not db_df.empty else 0
                self.status_var.set(
                    f"Plot updated: API data points: {api_count}, DB data points: {db_count}"
                )
        
        elif data_source == "Energy Comparative":
            # Create two subplots for comparative energy visualization
            # Process API server data (java processes)
            api_df = self._process_energy_data(filtered_api_data, "java", window_size_ms)
            
            # Process DB server data (postgres processes)
            db_df = self._process_energy_data(filtered_db_data, "postgres", window_size_ms)
            
            # Create a figure with two subplots (2 rows, 1 column)
            ax1 = self.fig.add_subplot(211)  # Top subplot
            ax2 = self.fig.add_subplot(212)  # Bottom subplot
            
            # Configure the axes
            ax1.set_title(f'Energy Consumption - API Server (Java) - {experiment_id}', fontsize=10)
            ax1.set_ylabel('Energy Consumption', fontsize=9)
            
            ax2.set_title(f'Energy Consumption - DB Server (Postgres) - {experiment_id}', fontsize=10)
            ax2.set_xlabel('Time (EET)', fontsize=9)
            ax2.set_ylabel('Energy Consumption', fontsize=9)
            
            # Format time axes
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S', tz=self.display_timezone))
            ax1.tick_params(axis='x', rotation=45)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S', tz=self.display_timezone))
            ax2.tick_params(axis='x', rotation=45)
            
            # Plot API server data in top subplot
            if api_df.empty:
                ax1.text(0.5, 0.5, "No API server energy data available", 
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax1.transAxes, fontsize=10)
            else:
                if accumulation_mode == "Simple":
                    # Simple plot - just show the data points
                    if plot_type == "Line":
                        ax1.plot(api_df['datetime'], api_df['consumption'], 
                                color='red', linewidth=2, marker=None)
                    elif plot_type == "Scatter":
                        ax1.scatter(api_df['datetime'], api_df['consumption'], 
                                   color='blue', marker='o', s=20)
                    elif plot_type == "Bar":
                        bar_width = 0.0002  # Adjust as needed
                        ax1.bar(api_df['datetime'], api_df['consumption'], 
                               width=bar_width, color='blue', alpha=0.7)
                else:  # Accumulated mode
                    # Add a cumulative sum column for accumulated energy over time
                    api_df['accumulated'] = api_df['consumption'].cumsum()
                    
                    if plot_type == "Line":
                        ax1.plot(api_df['datetime'], api_df['accumulated'], 
                                color='red', linewidth=2, marker=None, label='Accumulated')
                        # Add a second y-axis for non-accumulated values
                        ax1_twin = ax1.twinx()
                        ax1_twin.plot(api_df['datetime'], api_df['consumption'], 
                                     color='lightcoral', linewidth=1.5, marker=None, alpha=0.7, label='Per Interval')
                        ax1_twin.set_ylabel('Interval Energy', color='lightcoral', fontsize=8)
                        ax1_twin.tick_params(axis='y', labelcolor='lightcoral')
                    elif plot_type == "Bar":
                        bar_width = 0.0002  # Adjust as needed
                        ax1.fill_between(api_df['datetime'], api_df['accumulated'], color='blue', alpha=0.3, label='Accumulated')
                        ax1.plot(api_df['datetime'], api_df['accumulated'], color='blue', linewidth=1.5)
                        # Add bars for non-accumulated values
                        ax1_twin = ax1.twinx()
                        ax1_twin.bar(api_df['datetime'], api_df['consumption'], width=bar_width, color='lightblue', alpha=0.7, label='Per Interval')
                        ax1_twin.set_ylabel('Interval Energy', color='lightblue', fontsize=8)
                        ax1_twin.tick_params(axis='y', labelcolor='lightblue')
                    elif plot_type == "Scatter":
                        ax1.scatter(api_df['datetime'], api_df['accumulated'], color='blue', marker='o', s=15, label='Accumulated')
                        ax1.plot(api_df['datetime'], api_df['accumulated'], color='blue', linewidth=1, alpha=0.5)
            
            # Plot DB server data in bottom subplot
            if db_df.empty:
                ax2.text(0.5, 0.5, "No DB server energy data available", 
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax2.transAxes, fontsize=10)
            else:
                if accumulation_mode == "Simple":
                    # Simple plot - just show the data points
                    if plot_type == "Line":
                        ax2.plot(db_df['datetime'], db_df['consumption'], 
                                color='blue', linewidth=2, marker=None)
                    elif plot_type == "Scatter":
                        ax2.scatter(db_df['datetime'], db_df['consumption'], 
                                   color='green', marker='s', s=20)
                    elif plot_type == "Bar":
                        bar_width = 0.0002  # Adjust as needed
                        ax2.bar(db_df['datetime'], db_df['consumption'], 
                               width=bar_width, color='green', alpha=0.7)
                else:  # Accumulated mode
                    # Add a cumulative sum column for accumulated energy over time
                    db_df['accumulated'] = db_df['consumption'].cumsum()
                    
                    if plot_type == "Line":
                        ax2.plot(db_df['datetime'], db_df['accumulated'], 
                                color='blue', linewidth=2, marker=None, label='Accumulated')
                        # Add a second y-axis for non-accumulated values
                        ax2_twin = ax2.twinx()
                        ax2_twin.plot(db_df['datetime'], db_df['consumption'], 
                                     color='lightblue', linewidth=1.5, marker=None, alpha=0.7, label='Per Interval')
                        ax2_twin.set_ylabel('Interval Energy', color='lightblue', fontsize=8)
                        ax2_twin.tick_params(axis='y', labelcolor='lightblue')
                    elif plot_type == "Bar":
                        bar_width = 0.0002  # Adjust as needed
                        ax2.fill_between(db_df['datetime'], db_df['accumulated'], color='green', alpha=0.3, label='Accumulated')
                        ax2.plot(db_df['datetime'], db_df['accumulated'], color='green', linewidth=1.5)
                        # Add bars for non-accumulated values
                        ax2_twin = ax2.twinx()
                        ax2_twin.bar(db_df['datetime'], db_df['consumption'], width=bar_width, color='lightblue', alpha=0.7, label='Per Interval')
                        ax2_twin.set_ylabel('Interval Energy', color='lightblue', fontsize=8)
                        ax2_twin.tick_params(axis='y', labelcolor='lightblue')
                    elif plot_type == "Scatter":
                        ax2.scatter(db_df['datetime'], db_df['accumulated'], color='green', marker='s', s=15, label='Accumulated')
                        ax2.plot(db_df['datetime'], db_df['accumulated'], color='green', linewidth=1, alpha=0.5)
            
            # Add grid to both subplots
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            # Use scientific notation for y-axis if values are large
            if not api_df.empty and (api_df['consumption'].max() > 10000 or 
                                    (accumulation_mode == "Accumulated" and api_df['accumulated'].max() > 10000)):
                ax1.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
            
            if not db_df.empty and (db_df['consumption'].max() > 10000 or 
                                   (accumulation_mode == "Accumulated" and db_df['accumulated'].max() > 10000)):
                ax2.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
            
            # Add legends if needed
            if accumulation_mode == "Accumulated" and not api_df.empty:
                lines, labels = ax1.get_legend_handles_labels()
                lines2, labels2 = ax1.twinx().get_legend_handles_labels()
                ax1.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=8)
            
            if accumulation_mode == "Accumulated" and not db_df.empty:
                lines, labels = ax2.get_legend_handles_labels()
                lines2, labels2 = ax2.twinx().get_legend_handles_labels()
                ax2.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=8)
            
            # Adjust the layout to fit the subplots
            self.fig.tight_layout()
            
            # Update status with data summary
            api_count = len(api_df) if not api_df.empty else 0
            db_count = len(db_df) if not db_df.empty else 0
            total_api = api_df['consumption'].sum() if not api_df.empty else 0
            total_db = db_df['consumption'].sum() if not db_df.empty else 0
            
            # Format the summary message
            if accumulation_mode == "Accumulated":
                self.status_var.set(
                    f"Comparative view: API data: {api_count} points, total: {total_api:.2e} units | "
                    f"DB data: {db_count} points, total: {total_db:.2e} units"
                )
            else:
                self.status_var.set(
                    f"Comparative view: API data points: {api_count} | DB data points: {db_count}"
                )
                
        elif data_source == "Latency":
            # Plot latency data if available for the selected experiment
            experiment = self.data["benchmark_results"]["experiments"].get(experiment_id, {})
            runs = experiment.get("runs", [])
            
            if not runs:
                ax = self.fig.add_subplot(111)
                ax.text(0.5, 0.5, "No latency data available for this experiment", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
            else:
                # Create a new subplot
                ax = self.fig.add_subplot(111)
                
                # Configure the axis
                ax.set_xlabel('Time (EET)', fontsize=10)
                ax.set_ylabel('Latency (ms)', fontsize=10)
                ax.set_title(f'Request Latency for Experiment: {experiment_id}', fontsize=12)
                
                # Format the time axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S', tz=self.display_timezone))
                ax.tick_params(axis='x', rotation=45)
                
                # Collect latency data from all runs
                latency_data = []
                for run in runs:
                    if "latencies" in run:
                        for entry in run["latencies"]:
                            if "latency_ns" in entry and "timestamp" in entry:
                                timestamp_ms = entry["timestamp"]
                                latency_ms = entry["latency_ns"] / 1_000_000  # Convert ns to ms
                                dt = self._convert_to_eet(timestamp_ms)
                                latency_data.append((dt, latency_ms))
                
                if not latency_data:
                    ax.text(0.5, 0.5, "No detailed latency data available", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=ax.transAxes, fontsize=14)
                else:
                    # Convert to DataFrame for easier plotting
                    latency_df = pd.DataFrame(latency_data, columns=['datetime', 'latency'])
                    
                    # Plot based on plot type
                    if plot_type == "Line":
                        ax.plot(latency_df['datetime'], latency_df['latency'], 
                               color='purple', linewidth=2, marker=None, alpha=0.7)
                    elif plot_type == "Scatter":
                        ax.scatter(latency_df['datetime'], latency_df['latency'], 
                                 color='purple', marker='o', s=30, alpha=0.7)
                    elif plot_type == "Bar":
                        bar_width = 0.0002  # Adjust as needed
                        ax.bar(latency_df['datetime'], latency_df['latency'], 
                              width=bar_width, color='purple', alpha=0.7)
                    
                    # Add grid
                    ax.grid(True, linestyle='--', alpha=0.7)
                    
                    # Update status
                    self.status_var.set(f"Plotted {len(latency_data)} latency data points for experiment: {experiment_id}")
        
        elif data_source == "Throughput":
            # For throughput, we'll create a simple bar chart showing throughput per run
            experiment = self.data["benchmark_results"]["experiments"].get(experiment_id, {})
            runs = experiment.get("runs", [])
            
            if not runs:
                ax = self.fig.add_subplot(111)
                ax.text(0.5, 0.5, "No throughput data available for this experiment", 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
            else:
                # Create a new subplot
                ax = self.fig.add_subplot(111)
                
                # Configure the axis
                ax.set_xlabel('Run', fontsize=10)
                ax.set_ylabel('Throughput (req/s)', fontsize=10)
                ax.set_title(f'Throughput for Experiment: {experiment_id}', fontsize=12)
                
                # Collect throughput data
                run_labels = []
                throughput_values = []
                
                for i, run in enumerate(runs):
                    if "throughput" in run:
                        run_labels.append(f"Run {i+1}")
                        throughput_values.append(run["throughput"])
                
                if not throughput_values:
                    ax.text(0.5, 0.5, "No throughput data available", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=ax.transAxes, fontsize=14)
                else:
                    # Plot bar chart for throughput
                    ax.bar(run_labels, throughput_values, color='orange')
                    
                    # Add value labels on top of bars
                    for i, v in enumerate(throughput_values):
                        ax.text(i, v + 0.5, f"{v:.2f}", ha='center')
                    
                    # Update status
                    self.status_var.set(f"Plotted throughput for {len(throughput_values)} runs of experiment: {experiment_id}")
        
        # Draw the plot
        self.canvas.draw()
    
    def force_plot_update(self):
        """Force update the plot with the current experiment selection"""
        if not self.data or not self.experiment_var.get():
            self.status_var.set("No data loaded or no experiment selected")
            return
            
        # Simply call the update_plot method
        self.update_plot()
    
    def get_experiment_time_boundaries(self, experiment_id):
        """
        Extract time boundaries for the selected experiment.
        Returns: (start_time_ms, end_time_ms) in milliseconds since epoch, or None if not available
        """
        if not self.data or not experiment_id:
            return None, None
            
        if "benchmark_results" in self.data and "experiments" in self.data["benchmark_results"]:
            experiment = self.data["benchmark_results"]["experiments"].get(experiment_id, {})
            
            if not experiment or "runs" not in experiment or not experiment["runs"]:
                return None, None
                
            # Get the earliest start timestamp and latest end timestamp across all runs
            start_timestamps = []
            end_timestamps = []
            
            for run in experiment["runs"]:
                if "start_timestamp" in run:
                    start_timestamps.append(run["start_timestamp"])
                if "end_timestamp" in run:
                    end_timestamps.append(run["end_timestamp"])
                # If only start_timestamp but no end_timestamp, estimate using elapsed_time if available
                elif "start_timestamp" in run and "elapsed_time_ms" in run:
                    end_timestamps.append(run["start_timestamp"] + run["elapsed_time_ms"])
                    
            # If no explicit timestamps, try to use timestamp field which might be the end time
            if not start_timestamps and not end_timestamps:
                for run in experiment["runs"]:
                    if "timestamp" in run:
                        # This might be the end timestamp
                        end_timestamps.append(run["timestamp"])
                        # Estimate start time using elapsed_time if available
                        if "elapsed_time_ms" in run:
                            start_timestamps.append(run["timestamp"] - run["elapsed_time_ms"])
            
            if not start_timestamps and not end_timestamps:
                # If still no timestamps, we can't determine time boundaries - use the full range from energy data
                self.status_var.set(f"No explicit time boundaries found for {experiment_id}, using full energy data range.")
                
                # Look for any timestamps in the energy data
                api_energy_data = self.data.get("api_server_energy", [])
                db_energy_data = self.data.get("db_server_energy", [])
                
                energy_timestamps = []
                for entry in api_energy_data + db_energy_data:
                    if "timestamp" in entry:
                        # Convert seconds to milliseconds
                        energy_timestamps.append(entry.get("timestamp", 0) * 1000)
                
                if energy_timestamps:
                    # Use the full range of energy data
                    return min(energy_timestamps), max(energy_timestamps)
                
                return None, None
                
            # Take the min start time and max end time
            start_time_ms = min(start_timestamps) if start_timestamps else None
            end_time_ms = max(end_timestamps) if end_timestamps else None
            
            if start_time_ms is None and end_time_ms is not None:
                # If only have end time, estimate start time (30 seconds before)
                start_time_ms = end_time_ms - 30000
            elif end_time_ms is None and start_time_ms is not None:
                # If only have start time, estimate end time (30 seconds after)
                end_time_ms = start_time_ms + 30000
            
            # Add buffer time before and after (20% of experiment duration or at least 30 seconds)
            duration = end_time_ms - start_time_ms
            buffer = max(duration * 0.2, 30000)  # At least 30 seconds buffer
            
            return start_time_ms - buffer, end_time_ms + buffer
        
        return None, None
    
    def _filter_energy_data_by_time(self, energy_data, start_time_ms=None, end_time_ms=None):
        """
        Filter energy data to only include entries within the specified time range.
        
        Args:
            energy_data: List of energy data entries
            start_time_ms: Start time in milliseconds (inclusive)
            end_time_ms: End time in milliseconds (inclusive)
            
        Returns:
            Filtered list of energy data entries
        """
        if not energy_data:
            return []
            
        # If no time boundaries provided, return all data
        if start_time_ms is None or end_time_ms is None:
            self.status_var.set(f"No time boundaries provided - showing all {len(energy_data)} energy data points")
            return energy_data
            
        # Convert start/end times to seconds for comparison with energy timestamp (which is in seconds)
        start_time_sec = start_time_ms / 1000
        end_time_sec = end_time_ms / 1000
        
        # Convert to human-readable format for debugging
        start_time_str = self._convert_to_eet(start_time_ms).strftime('%Y-%m-%d %H:%M:%S')
        end_time_str = self._convert_to_eet(end_time_ms).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get min/max timestamps from the data for debugging
        energy_timestamps = [entry.get("timestamp", 0) for entry in energy_data if "timestamp" in entry]
        
        if not energy_timestamps:
            self.status_var.set("Warning: No timestamp fields found in energy data")
            return energy_data  # Return all data if no timestamps
        
        min_timestamp = min(energy_timestamps)
        max_timestamp = max(energy_timestamps)
        
        # Convert energy timestamps to human-readable format - note energy timestamps are in seconds
        min_time_str = self._convert_to_eet(min_timestamp * 1000, is_milliseconds=True).strftime('%Y-%m-%d %H:%M:%S')
        max_time_str = self._convert_to_eet(max_timestamp * 1000, is_milliseconds=True).strftime('%Y-%m-%d %H:%M:%S')
        
        # Print detailed debug information
        self.status_var.set(
            f"Experiment time: {start_time_str} to {end_time_str} | "
            f"Energy data: {min_time_str} to {max_time_str} | "
            f"Total entries: {len(energy_data)}"
        )
        
        # Check if there's any overlap at all
        if max_timestamp < start_time_sec or min_timestamp > end_time_sec:
            self.status_var.set(
                f"WARNING: No overlap between experiment time ({start_time_str} - {end_time_str}) "
                f"and energy data ({min_time_str} - {max_time_str}). "
                f"Showing ALL data instead."
            )
            return energy_data  # Return all data if no overlap
        
        # Use a VERY wide range for filtering to ensure we don't miss relevant data
        # This is especially important if timestamps might have slight mismatches
        # At most, limit to 1 hour before and after (but only if we have a lot of data)
        buffer_sec = min(3600, max(600, (end_time_sec - start_time_sec) * 2))
        expanded_start = max(min_timestamp, start_time_sec - buffer_sec)
        expanded_end = min(max_timestamp, end_time_sec + buffer_sec)
        
        # Convert to human-readable format
        expanded_start_str = self._convert_to_eet(expanded_start * 1000, is_milliseconds=True).strftime('%Y-%m-%d %H:%M:%S')
        expanded_end_str = self._convert_to_eet(expanded_end * 1000, is_milliseconds=True).strftime('%Y-%m-%d %H:%M:%S')
        
        # Print the expanded range
        self.status_var.set(
            f"Using expanded time range: {expanded_start_str} to {expanded_end_str} "
            f"(buffer: {buffer_sec:.2f}s)"
        )
        
        # Filter data to only include entries within the expanded time range
        filtered_data = [
            entry for entry in energy_data 
            if entry.get("timestamp", 0) >= expanded_start and entry.get("timestamp", 0) <= expanded_end
        ]
        
        if not filtered_data:
            self.status_var.set(
                f"WARNING: No energy data found after filtering. "
                f"Showing ALL data instead."
            )
            return energy_data
        
        # Show how many data points were kept
        self.status_var.set(
            f"Filtered energy data: kept {len(filtered_data)}/{len(energy_data)} entries "
            f"({(len(filtered_data)/len(energy_data)*100):.1f}%)"
        )
        
        return filtered_data
    
    def _process_energy_data(self, data_source, process_type, window_size_ms):
        """Process energy data with time-based windowing
        
        Args:
            data_source: List of energy data entries
            process_type: Type of process to filter by ("java" or "postgres")
            window_size_ms: Size of accumulation window in milliseconds
            
        Returns:
            DataFrame with processed data
        """
        # Initialize variables for accumulation
        current_window_start = None
        accumulated_consumption = 0.0
        processed_data = []
        
        for entry in data_source:
            cmdline = entry.get("cmdline", "")
            exe = entry.get("exe", "")
            
            # Skip scaphandre processes and empty entries
            if "scaphandre" in cmdline or "scaphandre" in exe or (not cmdline and not exe):
                continue
                
            # Filter based on process type
            is_relevant_process = (process_type == "postgres" and "postgres" in cmdline) or \
                                 (process_type == "java" and ("java" in cmdline or "java" in exe))
                                 
            if not is_relevant_process:
                continue
                
            consumption = entry.get("consumption", 0.0)
            
            # Energy timestamps are in seconds - convert to milliseconds for consistency with benchmark timestamps
            timestamp = entry.get("timestamp", 0.0)
            milliseconds = int(timestamp * 1000)  # Convert seconds to milliseconds
            
            if current_window_start is None or milliseconds >= current_window_start + window_size_ms:
                if current_window_start is not None:
                    processed_data.append((current_window_start, accumulated_consumption))
                current_window_start = milliseconds
                accumulated_consumption = consumption
            else:
                accumulated_consumption += consumption
                
        # Add final point
        if current_window_start is not None:
            processed_data.append((current_window_start, accumulated_consumption))
            
        # Convert processed data to DataFrame
        df = pd.DataFrame(processed_data, columns=['timestamp', 'consumption'])
        
        # Important: Use the same timestamp conversion approach as in experiment details
        # Convert the millisecond timestamps to EET datetime objects
        datetime_values = []
        for ts in df['timestamp']:
            # All timestamps are now in milliseconds format consistently
            datetime_values.append(self._convert_to_eet(ts))
            
        df['datetime'] = datetime_values
        
        return df
    
    def _convert_to_eet(self, timestamp, is_milliseconds=True):
        """Convert timestamp to EET datetime object
        
        Args:
            timestamp: Timestamp (in milliseconds by default)
            is_milliseconds: Whether the timestamp is in milliseconds (True) or seconds (False)
        
        Returns:
            Datetime object in EET timezone
        """
        if is_milliseconds:
            timestamp = timestamp / 1000  # Convert ms to seconds
            
        # Create UTC datetime object
        utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        # Convert to EET timezone (UTC+2 or UTC+3 depending on DST)
        eet_dt = utc_dt.astimezone(self.display_timezone)
        
        return eet_dt

if __name__ == "__main__":
    root = tk.Tk()
    app = ExperimentVisualizer(root)
    root.mainloop() 