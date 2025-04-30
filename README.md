# RestQFramework Project Documentation

## Overview

RestQFramework is a project designed for benchmarking RESTful APIs with a focus on performance and energy consumption analysis. It combines Ansible for automated benchmark execution, Java-based components for the core API and potentially shared logic, and a Python-based visualizer to analyze the results gathered during experiments.

The framework appears to support collecting energy data from both Scaphandre and PowerAPI, allowing for comparative analysis.

## Components

### 1. Ansible Benchmark (`ansible-benchmark/`)

This directory contains the infrastructure and logic for running the benchmarks using Ansible.

**Purpose:** Automates the setup, execution, and potentially teardown of benchmark experiments against the target API.

**Key Files & Directories:**

*   `playbook.yml` / `playbook-*.yml`: The main Ansible playbooks defining the tasks to run the benchmark (e.g., setting up services, running the benchmark client, collecting results). It seems there might be variations or older versions (`playbook-1.yml`, `playbook-gross.yml`).
*   `inventory.yml` / `inventory-gross.yml`: Ansible inventory files defining the hosts (servers) involved in the benchmark (e.g., where the API server, DB server, and benchmark client run).
*   `benchmark-config.xml`: Configuration file for the benchmark tool itself (likely defining endpoints, request rates, duration, etc.).
*   `run_benchmark_*.sh`: Shell scripts likely used to trigger the Ansible playbooks (`ansible-playbook ...`) for specific environments (e.g., `lille`, `nancy`).
*   `docker-api/`, `docker-db/`: These directories suggest that the API and database components are run within Docker containers, managed possibly by the Ansible playbooks.
*   `INTEL/`, `AMD/`: These directories (and associated `.zip` files) might contain specific configurations, results, or drivers related to benchmarking on Intel and AMD hardware platforms.

### 2. API HTTP (`api-http/`)

This directory contains the source code for the HTTP API service that is being benchmarked.

**Purpose:** Provides the RESTful endpoints that the benchmark tool interacts with.

**Technology:**

*   **Language:** Java (indicated by `src/` and `pom.xml`).
*   **Build Tool:** Maven (indicated by `pom.xml`). The `pom.xml` defines dependencies, build process, and project metadata.
*   **Structure:** Standard Maven project layout (`src/main/java`, `src/test/java`, etc.).

### 3. Core (`core/`)

This directory likely contains shared core logic or components used by other parts of the project, potentially the `api-http` service.

**Purpose:** Encapsulates common functionalities, data structures, or utilities needed by the API or other modules.

**Technology:**

*   **Language:** Java (indicated by `src/` and `pom.xml`).
*   **Build Tool:** Maven (indicated by `pom.xml`). It's likely a dependency for the `api-http` project.

### 4. Experiment Visualizer (`visualizer_containers.py`)

This is a Python script responsible for visualizing the data collected from benchmark experiments.

**Purpose:** To load, process, and display performance metrics (latency, throughput) and energy consumption data (Scaphandre, PowerAPI) from the benchmark runs in an interactive GUI.

**Technology:**

*   **Language:** Python
*   **GUI:** Tkinter (`tkinter`, `ttk`)
*   **Data Handling:** Pandas, NumPy, JSON
*   **Plotting:** Matplotlib, Plotly
*   **Timezones:** Pytz

**Key Features:**

*   **Data Loading:** Loads experiment results from a JSON file.
*   **Expected JSON Structure:** The script expects a top-level JSON object with keys like:
    *   `api_server_energy`: List of energy readings from the machine running the API server (likely Scaphandre format).
    *   `db_server_energy`: List of energy readings from the machine running the DB server (likely Scaphandre format).
    *   `benchmark_results`: Contains details about experiments, runs, configurations, latencies, and throughput.
    *   `container_info`: (Optional but recommended) Contains `api_container_id` and `db_container_id` to help filter Scaphandre energy data.
*   **Experiment Selection:** Allows users to select individual experiments or view data for "All Experiments".
*   **Details Display:** Shows configuration details and summary statistics for the selected experiment(s).
*   **Interactive Plotting:**
    *   Visualizes Energy Consumption (Scaphandre vs. PowerAPI), Total Energy Consumed, Latency, and Throughput.
    *   Supports different plot types (Line, Bar, Scatter).
    *   Allows filtering/comparison of energy data from Scaphandre (Host, API container, DB container) and PowerAPI (via separate JSON files).
    *   Features windowing/accumulation options for energy data.
    *   Highlights individual benchmark run periods on the plots.
    *   Includes controls for zooming, panning, and saving plots.
*   **Timezone Handling:** Displays timestamps in EET (Europe/Helsinki).

## Setup

*(Detailed setup instructions would need more information about dependencies and environment requirements)*

**General Steps:**

1.  **Ansible:**
    *   Install Ansible.
    *   Ensure necessary collections are installed (if any).
    *   Configure SSH access to target hosts defined in the inventory.
    *   Install Docker on target hosts if containers are used.
2.  **Java Components (`api-http`, `core`):**
    *   Install Java Development Kit (JDK) compatible with the projects.
    *   Install Apache Maven.
    *   Build the projects: `mvn clean install` in both `core` and `api-http` directories. This will produce JAR or WAR files.
3.  **Visualizer (`visualizer_containers.py`):**
    *   Install Python 3.
    *   Install required Python packages: `pip install pandas numpy pytz matplotlib plotly tk` (Note: `tk` might be included with Python on some systems).
4.  **Energy Monitoring (if used):**
    *   **Scaphandre:** Install and configure Scaphandre on the hosts where energy is measured. Ensure its output format matches what the visualizer expects.
    *   **PowerAPI:** Install and configure PowerAPI, MongoDB (or another supported sink), and ensure data is exported in the JSON format expected by the visualizer's browse function.

## Usage

*(Detailed usage instructions require more context)*

**General Workflow:**

1.  **Configure Benchmark:** Modify `ansible-benchmark/benchmark-config.xml` and `ansible-benchmark/inventory.yml` according to your target environment and benchmark parameters.
2.  **Build/Deploy API:** Ensure the latest versions of `api-http` (and `core`) are built and deployable (e.g., as Docker images if used).
3.  **Run Benchmark:** Execute the appropriate `run_benchmark_*.sh` script or run the Ansible playbook directly: `ansible-playbook -i inventory.yml playbook.yml`.
4.  **Collect Results:** The Ansible playbook should collect the benchmark results (performance data, energy data) into a structured format, ideally the JSON file expected by the visualizer.
5.  **Visualize Results:**
    *   Run the visualizer: `python visualizer_containers.py`.
    *   Click "Load Data" and select the JSON results file from the benchmark run.
    *   If using PowerAPI data, browse and load the respective API and DB server energy JSON files using the "Browse" buttons in the "PowerAPI Energy Data" section. Select the correct target service from the dropdowns.
    *   Select an experiment from the "Select Experiment" dropdown.
    *   Use the plot controls (Plot Type, Data Source, Accumulation, Window Size, Host Energy visibility) to explore the data.
    *   Analyze the displayed details and plots.

## Contributing

*(Placeholder - Add contribution guidelines if applicable)*

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.



