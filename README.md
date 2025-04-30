# RestQFramework Project Documentation

## Overview

RestQFramework is a project for benchmarking RESTful APIs, focusing on performance and energy consumption. It uses Ansible to automate benchmark runs, Java for the core API and related components, and a Python-based visualizer to analyze the results.

The framework can collect energy data from both Scaphandre and PowerAPI, allowing for comparisons.

## Components

### 1. Ansible Benchmark (`ansible-benchmark/`)

This directory holds the Ansible setup for running the benchmarks.

**Purpose:** Automates running benchmark experiments against the target API, including setup and result collection.

**Key Files & Directories:**

*   `playbook.yml` / `playbook-*.yml`: The main Ansible playbooks listing the tasks for the benchmark (e.g., setting up services, running the client, gathering results). Variations like `playbook-1.yml` and `playbook-gross.yml` might exist.
*   `inventory.yml` / `inventory-gross.yml`: Ansible inventory files listing the servers involved (API server, DB server, benchmark client, etc.).
*   `benchmark-config.xml`: Configuration file for the benchmark tool itself, specifying endpoints, request rates, duration, etc.
*   `run_benchmark_*.sh`: Shell scripts used to start the Ansible playbooks for specific environments (e.g., `lille`, `nancy`).
*   `docker-api/`, `docker-db/`: These directories indicate that the API and database components run inside Docker containers, managed by the Ansible playbooks.
*   `INTEL/`, `AMD/`: These directories (and related `.zip` files) contain specific configurations, results, or drivers for benchmarking on Intel and AMD hardware.

### 2. API HTTP (`api-http/`)

This directory contains the source code for the HTTP API service being benchmarked.

**Purpose:** Provides the RESTful endpoints that the benchmark tool calls.

**Technology:**

*   **Language:** Java, Python (for visualization)
*   **Build Tool:** Maven (`pom.xml` defines dependencies, build process, etc.)
*   **Structure:** Standard Maven project (`src/main/java`, `src/test/java`, etc.).

### 3. Core (`core/`)

This directory contains shared core logic used by other parts of the project, such as the `api-http` service.

**Purpose:** Holds common functions, data structures, or utilities.

**Technology:**

*   **Language:** Java
*   **Build Tool:** Maven (`pom.xml`). It serves as a dependency for the `api-http` project.

### 4. Experiment Visualizer (`visualizer_containers.py`)

This Python script visualizes the data collected from benchmark runs.

**Purpose:** Loads, processes, and displays performance metrics (latency, throughput) and energy consumption data (Scaphandre, PowerAPI) using an interactive GUI.

**Technology:**

*   **Language:** Python
*   **GUI:** Tkinter (`tkinter`, `ttk`)
*   **Data Handling:** Pandas, NumPy, JSON
*   **Plotting:** Matplotlib, Plotly
*   **Timezones:** Pytz

**Key Features:**

*   **Data Loading:** Loads experiment results from a JSON file.
*   **Expected JSON Structure:** The script reads a top-level JSON object with keys like:
    *   `api_server_energy`: List of energy readings (Scaphandre format) from the API server machine.
    *   `db_server_energy`: List of energy readings (Scaphandre format) from the DB server machine.
    *   `benchmark_results`: Contains experiment details, runs, configurations, latencies, and throughput.
    *   `container_info`: (Optional) Contains `api_container_id` and `db_container_id` to help filter Scaphandre energy data for specific containers.
*   **Experiment Selection:** Users can select individual experiments or view combined data for "All Experiments".
*   **Details Display:** Shows configuration details and summary statistics for selected experiments.
*   **Interactive Plotting:**
    *   Visualizes Energy Consumption (Scaphandre vs. PowerAPI), Total Energy Consumed, Latency, and Throughput.
    *   Supports Line, Bar, and Scatter plot types.
    *   Allows comparing Scaphandre energy data (Host, API container, DB container) with PowerAPI data (loaded from separate JSON files).
    *   Offers windowing/accumulation options for energy data.
    *   Highlights benchmark run periods on the plots.
    *   Includes controls for zoom, pan, and saving plots.
*   **Timezone Handling:** Displays timestamps in EET (Europe/Helsinki).

## Setup

*(Specific dependency versions and environment details are needed for full setup instructions)*

**General Steps:**

1.  **Ansible:**
    *   Install Ansible.
    *   Install any required Ansible collections.
    *   Set up SSH access to the target hosts listed in the inventory.
    *   Install Docker on target hosts if using containers.
2.  **Java Components (`api-http`, `core`):**
    *   Install a compatible Java Development Kit (JDK).
    *   Install Apache Maven.
    *   Build the projects using `mvn clean install` in the `core` and `api-http` directories.
3.  **Visualizer (`visualizer_containers.py`):**
    *   Install Python 3.
    *   Install required Python packages: `pip install pandas numpy pytz matplotlib plotly tk` (`tk` might be included with your Python install).
4.  **Energy Monitoring Tools (If Used):**
    *   **Scaphandre:** Install and run Scaphandre on the hosts you want to monitor. Make sure its output format matches the visualizer's expectations.
    *   **PowerAPI:** Install PowerAPI and a supported sink (like MongoDB). Configure it to export data in the JSON format the visualizer can load.

## Usage

*(More specific steps depend on the exact benchmark configuration)*

**General Workflow:**

1.  **Configure Benchmark:** Edit `ansible-benchmark/benchmark-config.xml` and `ansible-benchmark/inventory.yml` for your environment and desired benchmark settings.
2.  **Build/Deploy API:** Make sure the latest `api-http` and `core` modules are built and ready for deployment (e.g., as Docker images).
3.  **Run Benchmark:** Run the relevant `run_benchmark_*.sh` script or execute the Ansible playbook directly: `ansible-playbook -i inventory.yml playbook.yml`.
4.  **Collect Results:** Ansible should gather the performance and energy data into the JSON file format needed by the visualizer.
5.  **Visualize Results:**
    *   Start the visualizer: `python visualizer_containers.py`.
    *   Click "Load Data" and choose the JSON results file.
    *   If using PowerAPI, load the API and DB server energy JSON files using the "Browse" buttons under "PowerAPI Energy Data". Select the correct target service from the dropdowns.
    *   Choose an experiment from the "Select Experiment" list.
    *   Use the controls (Plot Type, Data Source, Accumulation, etc.) to explore the data plots.
    *   Review the details and plots.

## Contributing

*(Add specific contribution guidelines here if available)*

Pull requests are welcome. For major changes, please open an issue first to discuss your proposed changes.

Remember to update tests as needed.



