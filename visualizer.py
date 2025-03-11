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
import matplotlib.ticker as mticker

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
                
                # Add "All Experiments" as the first option
                all_experiments_option = "All Experiments"
                self.experiment_selector['values'] = [all_experiments_option] + experiment_ids
                
                # Select the first option (All Experiments)
                self.experiment_selector.current(0)
                self.experiment_var.set(all_experiments_option)
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
        
        # Handle "All Experiments" selection
        if experiment_id == "All Experiments":
            if "benchmark_results" in self.data and "experiments" in self.data["benchmark_results"]:
                experiments = self.data["benchmark_results"]["experiments"]
                
                # Display a summary of all experiments
                row = 0
                ttk.Label(self.details_frame, text="All Experiments Summary", font=("Arial", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
                row += 1
                
                ttk.Label(self.details_frame, text=f"Total Experiments: {len(experiments)}", font=("Arial", 10)).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
                row += 1
                
                # Add a brief overview of each experiment
                for exp_id, exp_data in experiments.items():
                    ttk.Label(self.details_frame, text=f"Experiment: {exp_id}", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
                    row += 1
                    
                    runs_count = len(exp_data.get("runs", []))
                    ttk.Label(self.details_frame, text=f"Runs: {runs_count}", font=("Arial", 10)).grid(row=row, column=0, sticky=tk.W, padx=20, pady=2)
                    row += 1
                    
                    if "duration_seconds" in exp_data:
                        ttk.Label(self.details_frame, text=f"Duration: {exp_data['duration_seconds']} seconds", font=("Arial", 10)).grid(row=row, column=0, sticky=tk.W, padx=20, pady=2)
                        row += 1
                    
                    if "requests_per_second" in exp_data:
                        ttk.Label(self.details_frame, text=f"Rate: {exp_data['requests_per_second']} req/s", font=("Arial", 10)).grid(row=row, column=0, sticky=tk.W, padx=20, pady=2)
                        row += 1
                    
                    # Add a separator
                    ttk.Separator(self.details_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
                    row += 1
            
            # Update the plot with all experiments
            self.update_plot()
            return
            
        # Regular single experiment selection
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
        self.status_var.set(f"Updating plot for: {experiment_id}")
        self.root.update_idletasks()  # Force UI update
        
        # Clear the figure
        self.fig.clear()
        
        # Get the experiment time boundaries
        if experiment_id == "All Experiments":
            # Get the combined time boundaries for all experiments
            start_time_ms, end_time_ms = self.get_all_experiments_time_boundaries()
            
            # Get the list of all experiment IDs
            experiment_ids = list(self.data["benchmark_results"]["experiments"].keys())
        else:
            # Get boundaries for the single selected experiment
            start_time_ms, end_time_ms = self.get_experiment_time_boundaries(experiment_id)
            experiment_ids = [experiment_id]
        
        # Debug info - show time boundaries in human-readable format
        if start_time_ms is not None and end_time_ms is not None:
            start_time_eet = self._convert_to_eet(start_time_ms).strftime('%Y-%m-%d %H:%M:%S')
            end_time_eet = self._convert_to_eet(end_time_ms).strftime('%Y-%m-%d %H:%M:%S')
            self.status_var.set(f"Time bounds: {start_time_eet} to {end_time_eet} (EET)")
            self.root.update_idletasks()
        
        # Filter energy data to only include entries within the time range
        api_energy_data = self.data.get("api_server_energy", [])
        db_energy_data = self.data.get("db_server_energy", [])
        
        filtered_api_data = self._filter_energy_data_by_time(api_energy_data, start_time_ms, end_time_ms)
        filtered_db_data = self._filter_energy_data_by_time(db_energy_data, start_time_ms, end_time_ms)
        
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
            
            # Set plot title based on selected experiments
            if experiment_id == "All Experiments":
                ax.set_title(f'Energy Consumption for All Experiments', fontsize=12)
            else:
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
                               width=bar_width, label='API Server (Java)', color='red', alpha=0.7)
                    
                    if not db_df.empty:
                        ax.bar(db_df['datetime'], db_df['consumption'], 
                               width=bar_width, label='DB Server (Postgres)', color='blue', alpha=0.7)
                
                elif plot_type == "Scatter":
                    if not api_df.empty:
                        ax.scatter(api_df['datetime'], api_df['consumption'], 
                                 label='API Server (Java)', color='red', marker='o', s=30)
                    
                    if not db_df.empty:
                        ax.scatter(db_df['datetime'], db_df['consumption'], 
                                  label='DB Server (Postgres)', color='blue', marker='x', s=30)
                
                # Add grid
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Add legend
                if not api_df.empty or not db_df.empty:
                    ax.legend(loc='best')
                
                # Add run boundaries visualization for each experiment
                experiment_colors = ['lightgreen', 'lightblue', 'lightyellow', 'lightpink', 'lightcoral', 'lightskyblue']
                
                for idx, exp_id in enumerate(experiment_ids):
                    run_boundaries = self._get_run_time_boundaries(exp_id)
                    if run_boundaries:
                        color_index = idx % len(experiment_colors)
                        color = experiment_colors[color_index]
                        
                        for i, (run_num, run_start, run_end) in enumerate(run_boundaries):
                            # Convert timestamps to datetime objects for plotting
                            run_start_dt = self._convert_to_eet(run_start)
                            run_end_dt = self._convert_to_eet(run_end)
                            
                            # Add shaded region for this run
                            ax.axvspan(run_start_dt, run_end_dt, 
                                      alpha=0.3, 
                                      color=color, 
                                      label=f'{exp_id} - Run {run_num}' if i == 0 else "")
                            
                            # Add vertical lines at run boundaries
                            ax.axvline(x=run_start_dt, color='green', linestyle='--', alpha=0.7)
                            ax.axvline(x=run_end_dt, color='red', linestyle='--', alpha=0.7)
                            
                            # Only add text labels if we're showing a single experiment
                            # Otherwise, it gets too cluttered
                            if experiment_id != "All Experiments":
                                midpoint = run_start_dt + (run_end_dt - run_start_dt) / 2
                                y_pos = ax.get_ylim()[1] * 0.95  # Position near the top
                                ax.text(midpoint, y_pos, f'Run {run_num}', 
                                       ha='center', va='top', 
                                       bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'))
                
                # Apply tight layout to maximize plot area
                self.fig.tight_layout()
                
                # Add experiment boundary visualization when showing all experiments
                if experiment_id == "All Experiments":
                    chronology = self._get_experiment_chronology()
                    
                    if len(chronology) > 1:  # Only need to show boundaries if there's more than one experiment
                        # Visualize the pause between experiments
                        for i in range(len(chronology) - 1):
                            current_exp_id, _, current_end = chronology[i]
                            next_exp_id, next_start, _ = chronology[i + 1]
                            
                            # Only show pause if there is a gap between experiments
                            if next_start > current_end:
                                # Convert to datetime for plotting
                                current_end_dt = self._convert_to_eet(current_end)
                                next_start_dt = self._convert_to_eet(next_start)
                                
                                # Add a gray shaded region for the pause
                                ax.axvspan(current_end_dt, next_start_dt, 
                                          alpha=0.2, 
                                          color='gray', 
                                          hatch='///' if i % 2 == 0 else '\\\\\\',
                                          label='Inter-experiment pause' if i == 0 else "")
                                
                                # Add vertical lines at experiment boundaries
                                ax.axvline(x=current_end_dt, color='black', linestyle='-', alpha=0.7, linewidth=2)
                                ax.axvline(x=next_start_dt, color='black', linestyle='-', alpha=0.7, linewidth=2)
                                
                                # Calculate the duration of the pause in seconds
                                pause_duration = (next_start - current_end) / 1000  # Convert ms to seconds
                                
                                # Add a text label for the pause duration
                                if pause_duration > 5:  # Only label if pause is significant (> 5 seconds)
                                    midpoint = current_end_dt + (next_start_dt - current_end_dt) / 2
                                    y_pos = ax.get_ylim()[1] * 0.75  # Position at 75% of the height
                                    
                                    # Format the duration
                                    if pause_duration < 60:
                                        duration_text = f"{pause_duration:.1f}s"
                                    elif pause_duration < 3600:
                                        duration_text = f"{pause_duration/60:.1f}min"
                                    else:
                                        duration_text = f"{pause_duration/3600:.1f}h"
                                    
                                    ax.text(midpoint, y_pos, 
                                           f"Pause: {duration_text}\n{current_exp_id} → {next_exp_id}", 
                                           ha='center', va='center', 
                                           bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'),
                                           fontsize=9)
                
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
                               width=bar_width, color='blue', alph=0.7)
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
            # Handle the "All Experiments" case
            if experiment_id == "All Experiments":
                # Create a new subplot
                ax = self.fig.add_subplot(111)
                
                # Configure the axis
                ax.set_xlabel('Time (EET)', fontsize=10)
                ax.set_ylabel('Latency (ms)', fontsize=10)
                ax.set_title(f'Request Latency for All Experiments', fontsize=12)
                
                # Format the time axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S', tz=self.display_timezone))
                ax.tick_params(axis='x', rotation=45)
                
                # Plot latency data for each experiment with different colors
                experiment_colors = ['purple', 'green', 'orange', 'brown', 'magenta', 'cyan']
                has_data = False
                
                for idx, exp_id in enumerate(experiment_ids):
                    experiment = self.data["benchmark_results"]["experiments"].get(exp_id, {})
                    runs = experiment.get("runs", [])
                    
                    # Collect latency data from all runs of this experiment
                    latency_data = []
                    for run in runs:
                        if "latencies" in run:
                            for entry in run["latencies"]:
                                if "latency_ns" in entry and "timestamp" in entry:
                                    timestamp_ms = entry["timestamp"]
                                    latency_ms = entry["latency_ns"] / 1_000_000  # Convert ns to ms
                                    dt = self._convert_to_eet(timestamp_ms)
                                    latency_data.append((dt, latency_ms))
                    
                    if latency_data:
                        has_data = True
                        # Convert to DataFrame for easier plotting
                        latency_df = pd.DataFrame(latency_data, columns=['datetime', 'latency'])
                        
                        # Plot based on plot type with experiment-specific color
                        color = experiment_colors[idx % len(experiment_colors)]
                        
                        if plot_type == "Line":
                            ax.plot(latency_df['datetime'], latency_df['latency'], 
                                   label=f'{exp_id}', color=color, linewidth=2, marker=None, alpha=0.7)
                        elif plot_type == "Scatter":
                            ax.scatter(latency_df['datetime'], latency_df['latency'], 
                                     label=f'{exp_id}', color=color, marker='o', s=30, alpha=0.7)
                        elif plot_type == "Bar":
                            bar_width = 0.0002  # Adjust as needed
                            ax.bar(latency_df['datetime'], latency_df['latency'], 
                                  width=bar_width, label=f'{exp_id}', color=color, alpha=0.7)
                
                if not has_data:
                    ax.text(0.5, 0.5, "No latency data available", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=ax.transAxes, fontsize=14)
                else:
                    # Add grid
                    ax.grid(True, linestyle='--', alpha=0.7)
                    
                    # Add legend for the experiments
                    ax.legend(loc='best')
                    
                    # Add run boundaries visualization for each experiment
                    experiment_colors = ['lightgreen', 'lightblue', 'lightyellow', 'lightpink', 'lightcoral', 'lightskyblue']
                    
                    for idx, exp_id in enumerate(experiment_ids):
                        run_boundaries = self._get_run_time_boundaries(exp_id)
                        if run_boundaries:
                            color_index = idx % len(experiment_colors)
                            color = experiment_colors[color_index]
                            
                            for i, (run_num, run_start, run_end) in enumerate(run_boundaries):
                                # Convert timestamps to datetime objects for plotting
                                run_start_dt = self._convert_to_eet(run_start)
                                run_end_dt = self._convert_to_eet(run_end)
                                
                                # Add shaded region for this run
                                ax.axvspan(run_start_dt, run_end_dt, 
                                          alpha=0.15,  # Lower alpha for multiple experiments
                                          color=color, 
                                          label="" if i > 0 else f'{exp_id} runs')
                                
                                # Add vertical lines at run boundaries (less visible)
                                ax.axvline(x=run_start_dt, color='green', linestyle='--', alpha=0.3)
                                ax.axvline(x=run_end_dt, color='red', linestyle='--', alpha=0.3)
                    
                    # Apply tight layout to maximize plot area
                    self.fig.tight_layout()
                    
                    # Add experiment boundary visualization when showing all experiments
                    chronology = self._get_experiment_chronology()
                    
                    if len(chronology) > 1:  # Only need to show boundaries if there's more than one experiment
                        # Visualize the pause between experiments
                        for i in range(len(chronology) - 1):
                            current_exp_id, _, current_end = chronology[i]
                            next_exp_id, next_start, _ = chronology[i + 1]
                            
                            # Only show pause if there is a gap between experiments
                            if next_start > current_end:
                                # Convert to datetime for plotting
                                current_end_dt = self._convert_to_eet(current_end)
                                next_start_dt = self._convert_to_eet(next_start)
                                
                                # Add a gray shaded region for the pause
                                ax.axvspan(current_end_dt, next_start_dt, 
                                          alpha=0.2, 
                                          color='gray', 
                                          hatch='///' if i % 2 == 0 else '\\\\\\',
                                          label='Inter-experiment pause' if i == 0 else "")
                                
                                # Add vertical lines at experiment boundaries
                                ax.axvline(x=current_end_dt, color='black', linestyle='-', alpha=0.7, linewidth=2)
                                ax.axvline(x=next_start_dt, color='black', linestyle='-', alpha=0.7, linewidth=2)
                                
                                # Calculate the duration of the pause in seconds
                                pause_duration = (next_start - current_end) / 1000  # Convert ms to seconds
                                
                                # Add a text label for the pause duration
                                if pause_duration > 5:  # Only label if pause is significant (> 5 seconds)
                                    midpoint = current_end_dt + (next_start_dt - current_end_dt) / 2
                                    y_pos = ax.get_ylim()[1] * 0.75  # Position at 75% of the height
                                    
                                    # Format the duration
                                    if pause_duration < 60:
                                        duration_text = f"{pause_duration:.1f}s"
                                    elif pause_duration < 3600:
                                        duration_text = f"{pause_duration/60:.1f}min"
                                    else:
                                        duration_text = f"{pause_duration/3600:.1f}h"
                                    
                                    ax.text(midpoint, y_pos, 
                                           f"Pause: {duration_text}\n{current_exp_id} → {next_exp_id}", 
                                           ha='center', va='center', 
                                           bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'),
                                           fontsize=9)
            else:
                # Single experiment latency view - use existing code
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
                        
                        # Add run boundaries visualization
                        if run_boundaries := self._get_run_time_boundaries(experiment_id):
                            # Define colors for alternating run shading
                            run_colors = ['lightgreen', 'lightblue']
                            
                            for i, (run_num, run_start, run_end) in enumerate(run_boundaries):
                                # Convert timestamps to datetime objects for plotting
                                run_start_dt = self._convert_to_eet(run_start)
                                run_end_dt = self._convert_to_eet(run_end)
                                
                                # Add shaded region for this run
                                ax.axvspan(run_start_dt, run_end_dt, 
                                          alpha=0.3, 
                                          color=run_colors[i % len(run_colors)], 
                                          label=f'Run {run_num}' if i == 0 else "")
                                
                                # Add vertical lines at run boundaries
                                ax.axvline(x=run_start_dt, color='green', linestyle='--', alpha=0.7)
                                ax.axvline(x=run_end_dt, color='red', linestyle='--', alpha=0.7)
                                
                                # Add text label for the run
                                midpoint = run_start_dt + (run_end_dt - run_start_dt) / 2
                                y_pos = ax.get_ylim()[1] * 0.95  # Position near the top
                                ax.text(midpoint, y_pos, f'Run {run_num}', 
                                       ha='center', va='top', 
                                       bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'))
                        
                        # Apply tight layout to maximize plot area
                        self.fig.tight_layout()
        
        elif data_source == "Throughput":
            # Handle the "All Experiments" case
            if experiment_id == "All Experiments":
                # Create a new subplot
                ax = self.fig.add_subplot(111)
                
                # Configure the axis
                ax.set_xlabel('Time (EET)', fontsize=10)
                ax.set_ylabel('Throughput (requests/second)', fontsize=10)
                ax.set_title(f'Request Throughput for All Experiments', fontsize=12)
                
                # Format the time axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S', tz=self.display_timezone))
                ax.tick_params(axis='x', rotation=45)
                
                # Format y-axis to show more decimal places
                ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.5f'))
                
                # Plot throughput data for each experiment with different colors
                experiment_colors = ['purple', 'green', 'orange', 'brown', 'magenta', 'cyan']
                has_data = False
                
                for idx, exp_id in enumerate(experiment_ids):
                    experiment = self.data["benchmark_results"]["experiments"].get(exp_id, {})
                    runs = experiment.get("runs", [])
                    
                    # Collect throughput data from all runs of this experiment
                    throughput_data = []
                    goodput_data = []
                    for run in runs:
                        if "throughput" in run and "start_timestamp" in run:
                            # Use the start timestamp for the throughput point
                            timestamp_ms = run["start_timestamp"]
                            throughput = run["throughput"]
                            dt = self._convert_to_eet(timestamp_ms)
                            throughput_data.append((dt, throughput))
                            
                            # Also collect goodput if available
                            if "goodput" in run:
                                goodput = run["goodput"]
                                goodput_data.append((dt, goodput))
                    
                    if throughput_data:
                        has_data = True
                        # Convert to DataFrame for easier plotting
                        throughput_df = pd.DataFrame(throughput_data, columns=['datetime', 'throughput'])
                        
                        # Sort by datetime to ensure chronological order
                        throughput_df = throughput_df.sort_values('datetime')
                        
                        # Plot with appropriate color and label
                        color = experiment_colors[idx % len(experiment_colors)]
                        if plot_type == "Line":
                            ax.plot(throughput_df['datetime'], throughput_df['throughput'], 
                                   marker='o', linestyle='-', color=color, 
                                   label=f"{exp_id} (Total)", linewidth=2)
                            
                            # Plot goodput if available
                            if goodput_data:
                                goodput_df = pd.DataFrame(goodput_data, columns=['datetime', 'goodput'])
                                goodput_df = goodput_df.sort_values('datetime')
                                ax.plot(goodput_df['datetime'], goodput_df['goodput'], 
                                       marker='x', linestyle='--', color=color, 
                                       label=f"{exp_id} (Successful)", linewidth=1.5, alpha=0.7)
                        elif plot_type == "Bar":
                            bar_width = 0.0002  # Adjust as needed
                            ax.bar(throughput_df['datetime'], throughput_df['throughput'], 
                                  width=bar_width, color=color, alpha=0.7, label=f"{exp_id} (Total)")
                            
                            # Plot goodput as bars if available
                            if goodput_data:
                                goodput_df = pd.DataFrame(goodput_data, columns=['datetime', 'goodput'])
                                goodput_df = goodput_df.sort_values('datetime')
                                # Use a lighter shade of the same color for goodput with slight offset
                                ax.bar(goodput_df['datetime'], goodput_df['goodput'], 
                                      width=bar_width*0.8, color=color, alpha=0.4, 
                                      label=f"{exp_id} (Successful)")
                        elif plot_type == "Scatter":
                            ax.scatter(throughput_df['datetime'], throughput_df['throughput'], 
                                      color=color, marker='o', s=50, label=f"{exp_id} (Total)")
                            
                            # Plot goodput if available
                            if goodput_data:
                                goodput_df = pd.DataFrame(goodput_data, columns=['datetime', 'goodput'])
                                goodput_df = goodput_df.sort_values('datetime')
                                ax.scatter(goodput_df['datetime'], goodput_df['goodput'], 
                                         color=color, marker='x', s=40, alpha=0.7,
                                         label=f"{exp_id} (Successful)")
                
                if has_data:
                    # Add a legend
                    ax.legend(loc='best', fontsize=8)
                    
                    # Set reasonable y-axis limits
                    if ax.get_ylim()[0] < 0:
                        ax.set_ylim(bottom=0)  # Start from 0 for throughput
                    
                    # Add data labels for Line and Scatter plots
                    if plot_type in ["Line", "Scatter"]:
                        for idx, exp_id in enumerate(experiment_ids):
                            experiment = self.data["benchmark_results"]["experiments"].get(exp_id, {})
                            runs = experiment.get("runs", [])
                            
                            # Process throughput data
                            throughput_data = []
                            for run in runs:
                                if "throughput" in run and "start_timestamp" in run:
                                    timestamp_ms = run["start_timestamp"]
                                    throughput = run["throughput"]
                                    dt = self._convert_to_eet(timestamp_ms)
                                    throughput_data.append((dt, throughput))
                            
                            if throughput_data:
                                throughput_df = pd.DataFrame(throughput_data, columns=['datetime', 'throughput'])
                                throughput_df = throughput_df.sort_values('datetime')
                                
                                # Add data labels
                                for i, row in throughput_df.iterrows():
                                    ax.text(row['datetime'], row['throughput'], f"{row['throughput']:.5f}", 
                                           ha='center', va='bottom', fontsize=7)
                else:
                    # No data available message
                    ax.text(0.5, 0.5, "No throughput data available for the selected experiments", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=ax.transAxes, fontsize=10)
            else:
                # Single experiment view
                experiment = self.data["benchmark_results"]["experiments"].get(experiment_id, {})
                runs = experiment.get("runs", [])
                
                # Create a new subplot
                ax = self.fig.add_subplot(111)
                
                # Configure the axis
                ax.set_xlabel('Run Number', fontsize=10)
                ax.set_ylabel('Throughput (requests/second)', fontsize=10)
                ax.set_title(f'Request Throughput for {experiment_id}', fontsize=12)
                
                # Format y-axis to show more decimal places
                ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.5f'))
                
                # Collect throughput data for this experiment
                throughput_data = []
                goodput_data = []
                for i, run in enumerate(runs):
                    run_number = i + 1
                    if "throughput" in run:
                        throughput = run["throughput"]
                        throughput_data.append((run_number, throughput))
                    if "goodput" in run:
                        goodput = run["goodput"]
                        goodput_data.append((run_number, goodput))
                
                if throughput_data or goodput_data:
                    # Plot throughput data
                    if throughput_data:
                        # Convert to DataFrame for easier plotting
                        throughput_df = pd.DataFrame(throughput_data, columns=['run', 'throughput'])
                        
                        # Plot with appropriate style
                        if plot_type == "Line":
                            ax.plot(throughput_df['run'], throughput_df['throughput'], 
                                  marker='o', linestyle='-', color='blue', 
                                  linewidth=2, label='Total Throughput')
                        elif plot_type == "Bar":
                            bar_width = 0.35
                            ax.bar(throughput_df['run'] - bar_width/2, throughput_df['throughput'], 
                                  width=bar_width, color='blue', alpha=0.7, label='Total Throughput')
                        elif plot_type == "Scatter":
                            ax.scatter(throughput_df['run'], throughput_df['throughput'], 
                                     color='blue', marker='o', s=50, label='Total Throughput')
                    
                    # Plot goodput data
                    if goodput_data:
                        # Convert to DataFrame for easier plotting
                        goodput_df = pd.DataFrame(goodput_data, columns=['run', 'goodput'])
                        
                        # Plot with appropriate style
                        if plot_type == "Line":
                            ax.plot(goodput_df['run'], goodput_df['goodput'], 
                                  marker='x', linestyle='--', color='green', 
                                  linewidth=2, label='Successful Throughput')
                        elif plot_type == "Bar":
                            bar_width = 0.35
                            ax.bar(goodput_df['run'] + bar_width/2, goodput_df['goodput'], 
                                  width=bar_width, color='green', alpha=0.7, label='Successful Throughput')
                        elif plot_type == "Scatter":
                            ax.scatter(goodput_df['run'], goodput_df['goodput'], 
                                     color='green', marker='x', s=50, label='Successful Throughput')
                    
                    # Add legend
                    ax.legend(loc='best')
                    
                    # Set x-axis to show integer run numbers
                    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
                    
                    # Set reasonable y-axis limits
                    if ax.get_ylim()[0] < 0:
                        ax.set_ylim(bottom=0)  # Start from 0 for throughput
                    
                    # Add data labels
                    if throughput_data and plot_type != "Bar":
                        for i, row in throughput_df.iterrows():
                            ax.text(row['run'], row['throughput'], f"{row['throughput']:.5f}", 
                                   ha='center', va='bottom', fontsize=8)
                    
                    if goodput_data and plot_type != "Bar":
                        for i, row in goodput_df.iterrows():
                            ax.text(row['run'], row['goodput'], f"{row['goodput']:.5f}", 
                                   ha='center', va='bottom', fontsize=8)
                else:
                    # No data available message
                    ax.text(0.5, 0.5, "No throughput data available for this experiment", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=ax.transAxes, fontsize=10)
        
        # Redraw the canvas with the new plot
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
        Uses the start timestamp of the first run and end timestamp of the last run.
        Returns: (start_time_ms, end_time_ms) in milliseconds since epoch, or None if not available
        """
        if not self.data or not experiment_id:
            return None, None
            
        if "benchmark_results" in self.data and "experiments" in self.data["benchmark_results"]:
            experiment = self.data["benchmark_results"]["experiments"].get(experiment_id, {})
            
            if not experiment or "runs" not in experiment or not experiment["runs"]:
                return None, None
            
            runs = experiment["runs"]
            if not runs:
                return None, None
                
            # Get the start timestamp from the first run
            first_run = runs[0]
            start_time_ms = first_run.get("start_timestamp")
            
            # Get the end timestamp from the last run
            last_run = runs[-1]
            end_time_ms = last_run.get("end_timestamp")
            
            # If end_timestamp is not available, try to calculate it from start_timestamp + elapsed_time_ms
            if end_time_ms is None and "start_timestamp" in last_run and "elapsed_time_ms" in last_run:
                end_time_ms = last_run["start_timestamp"] + last_run["elapsed_time_ms"]
            
            # If we still don't have valid timestamps, fall back to timestamp field
            if start_time_ms is None and "timestamp" in first_run:
                # If timestamp exists, assume it's the end time and try to calculate start time
                if "elapsed_time_ms" in first_run:
                    start_time_ms = first_run["timestamp"] - first_run["elapsed_time_ms"]
                else:
                    # No way to determine start time, just use timestamp
                    start_time_ms = first_run["timestamp"]
            
            if end_time_ms is None and "timestamp" in last_run:
                end_time_ms = last_run["timestamp"]
            
            # If we have valid timestamps, return them without any buffer
            if start_time_ms is not None and end_time_ms is not None:
                return start_time_ms, end_time_ms
            
            # If we can't determine the time boundaries, fall back to using energy data
            if start_time_ms is None or end_time_ms is None:
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
        
        # Filter data to only include entries within the exact experiment time range
        filtered_data = [
            entry for entry in energy_data 
            if entry.get("timestamp", 0) >= start_time_sec and entry.get("timestamp", 0) <= end_time_sec
        ]
        
        if not filtered_data:
            self.status_var.set(
                f"WARNING: No energy data found within the exact experiment timeframe. "
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

    def _get_run_time_boundaries(self, experiment_id):
        """
        Extract the time boundaries for each run in the experiment.
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            List of tuples (run_number, start_time_ms, end_time_ms)
        """
        if not self.data or "benchmark_results" not in self.data or "experiments" not in self.data["benchmark_results"]:
            return []
            
        experiment = self.data["benchmark_results"]["experiments"].get(experiment_id, {})
        if not experiment or "runs" not in experiment or not experiment["runs"]:
            return []
            
        run_boundaries = []
        for i, run in enumerate(experiment["runs"]):
            # Get start time
            start_time_ms = run.get("start_timestamp")
            
            # Get end time (either directly or calculated from start + elapsed)
            end_time_ms = run.get("end_timestamp")
            if end_time_ms is None and "start_timestamp" in run and "elapsed_time_ms" in run:
                end_time_ms = run["start_timestamp"] + run["elapsed_time_ms"]
            elif end_time_ms is None and "timestamp" in run:
                # If only timestamp exists (likely the end time), try to estimate start
                end_time_ms = run["timestamp"]
                if "elapsed_time_ms" in run:
                    start_time_ms = end_time_ms - run["elapsed_time_ms"]
            
            # Only include if we have both start and end times
            if start_time_ms is not None and end_time_ms is not None:
                run_boundaries.append((i+1, start_time_ms, end_time_ms))
        
        return run_boundaries

    def get_all_experiments_time_boundaries(self):
        """
        Get the time boundaries that encompass all experiments in the data.
        Returns: (start_time_ms, end_time_ms) in milliseconds since epoch, or None if not available
        """
        if not self.data or "benchmark_results" not in self.data or "experiments" not in self.data["benchmark_results"]:
            return None, None
            
        experiments = self.data["benchmark_results"]["experiments"]
        if not experiments:
            return None, None
            
        all_start_times = []
        all_end_times = []
        
        # Collect all timestamps from all experiments
        for experiment_id, experiment_data in experiments.items():
            start_time, end_time = self.get_experiment_time_boundaries(experiment_id)
            if start_time is not None:
                all_start_times.append(start_time)
            if end_time is not None:
                all_end_times.append(end_time)
        
        # Return the broadest range
        if all_start_times and all_end_times:
            return min(all_start_times), max(all_end_times)
        
        # Fallback to energy data if no experiment timestamps are available
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

    def _get_experiment_chronology(self):
        """
        Get the chronological ordering of experiments and identify the pauses between them.
        
        Returns:
            List of tuples (experiment_id, start_time_ms, end_time_ms) sorted by start time
        """
        if not self.data or "benchmark_results" not in self.data or "experiments" not in self.data["benchmark_results"]:
            return []
            
        experiments = self.data["benchmark_results"]["experiments"]
        if not experiments:
            return []
        
        # Collect time boundaries for each experiment
        experiment_times = []
        for experiment_id, experiment_data in experiments.items():
            start_time, end_time = self.get_experiment_time_boundaries(experiment_id)
            if start_time is not None and end_time is not None:
                experiment_times.append((experiment_id, start_time, end_time))
        
        # Sort experiments by start time
        experiment_times.sort(key=lambda x: x[1])
        
        return experiment_times

if __name__ == "__main__":
    root = tk.Tk()
    app = ExperimentVisualizer(root)
    root.mainloop() 