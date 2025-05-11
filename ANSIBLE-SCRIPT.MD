# Ansible Playbook for RestQFramework Benchmarking on Grid\'5000

## 1. Overview

This Ansible playbook automates the deployment, execution, and results collection for benchmarking the RestQFramework on the Grid\'5000 testbed. It sets up a 3-node environment:
1.  **Node 1 (DB Server)**: Hosts the PostgreSQL database, populated with TPC-H data using the `core` module. Energy consumption of this node and its containers is monitored.
2.  **Node 2 (API Server)**: Runs the `api-http` Spring Boot application, serving REST endpoints for TPC-H queries. Energy consumption is also monitored here.
3.  **Node 3 (Benchmark Client & Aggregator)**: Executes the `ApiBenchmark` tool (from the `api-http` module) to send HTTP requests to Node 2. It also serves as a temporary aggregation point for results before they are fetched to the Ansible controller.

The playbook handles:
-   Reserving nodes on Grid\'5000 and deploying a base OS image.
-   Installing necessary software (Java, Docker, Maven, Git, Scaphandre, MongoDB tools).
-   Cloning the RestQFramework repository.
-   Building the `core`, `benchbase`, and `api-http` Java modules from source.
-   Configuring and starting the PostgreSQL database with TPC-H data.
-   Configuring and starting the `api-http` application.
-   Setting up power/energy monitoring using Scaphandre and an external MongoDB-based solution (via `setup-formula-config.sh`).
-   Running the API benchmark based on `benchmark-config.xml`.
-   Collecting various logs and results: benchmark output, Scaphandre energy data, application logs, and power monitoring dumps from MongoDB.
-   Aggregating these results into a final combined JSON file.

This setup allows for repeatable performance and energy efficiency benchmarks of the RestQFramework.

## 2. Prerequisites

-   Ansible installed on the control machine.
-   Access to Grid\'5000 (credentials and CLI tools like `oarsub`, `kadeploy3` configured).
-   The `RestQFramework` repository should be accessible via HTTPS for cloning.
-   The `ansible-benchmark/playbook.yml` file and associated files (e.g., `benchmark-config.xml`, `docker-compose` files in `ansible-benchmark/docker-db` and `ansible-benchmark/docker-api`, `ansible-benchmark/INTEL/setup-formula-config.sh`) must be present in the expected locations relative to the playbook.

## 3. Key Variables

The playbook uses several variables, some of which need to be defined or can be customized:

-   `OS_image`: (Default: `ubuntu2204-x64-min`) The Grid\'5000 OS image to deploy on nodes.
-   `grid_time`: (Default: `"5:00:00"`) Walltime for the Grid\'5000 job reservation.
-   `grid_site`: The Grid\'5000 site to use (e.g., `nancy`, `rennes`). This should be defined when running the playbook, for example, via `--extra-vars "grid_site=nancy"`.
-   `timestamp`: A crucial variable used for naming results directories and files (e.g., `experiment_{{ timestamp }}`). This should be passed as an extra variable during playbook execution, for example, `--extra-vars "timestamp=$(date +%Y%m%d-%H%M%S)"`.
-   `scaphandre_timestep_s`: (Default not set in playbook, used in commands like `scaphandre json -s {{ scaphandre_timestep_s }}`) The sampling interval in seconds for Scaphandre energy measurements. This should be passed as an extra variable, e.g., `--extra-vars "scaphandre_timestep_s=1"`.
-   `postgres_container_name`: (Default: `db-docker-container`) Name for the PostgreSQL Docker container.
-   `postgres_image`: (Default: `postgres:14`) Docker image for PostgreSQL.
-   `postgres_password`: (Default: `password`) Password for the PostgreSQL `admin` user.
-   `tpch_db`: (Default: `tpchdb`) Name of the TPC-H database.
-   `postgres_port`: (Default: `5432`) Port for PostgreSQL.
-   `api_container_name`: (Default: `spring-api`) Name for the API server Docker container.
-   `api_port`: (Default: `8086`) Port for the API server application.

## 4. Playbook Structure and Execution Flow

The playbook is organized into several plays, each targeting specific hosts or groups.

### 4.1. Play 1: Initialize Grid\'5000
-   **Hosts**: `grid5000` (executed on the Ansible controller)
-   **Purpose**: Reserves three nodes on Grid\'5000 and deploys the specified OS image.
-   **Tasks**:
    1.  Reserves two "chifflot" nodes and one "other" node using `oarsub`. Chifflot nodes are typically equipped with power monitoring capabilities.
    2.  Extracts job IDs and assigned hostnames.
    3.  Assigns hostnames to `node1` (chifflot), `node2` (chifflot), and `node3` (other).
    4.  Adds these nodes to the in-memory Ansible inventory under the `reserved_nodes` group.
    5.  Deploys the `{{ OS_image }}` on all three nodes in parallel using `kadeploy3`.

### 4.2. Play 2: Setup Node 1 (DB Server)
-   **Hosts**: `node1`
-   **Remote User**: `root`
-   **Purpose**: Configures the first node as the database server.
-   **Tasks**:
    1.  **Java Installation**: Downloads and installs JDK 21.
    2.  **Docker Setup**: Installs Docker and Docker Compose.
    3.  **Repository Clone**: Clones the `RestQFramework` Git repository to `/root/RestQFramework`.
    4.  **PostgreSQL Database**:
        -   Starts a PostgreSQL container using `docker-compose up -d` with the configuration from `/root/RestQFramework/ansible-benchmark/docker-db/docker-compose.yml`. This sets up a PostgreSQL instance with user `admin`, password `{{ postgres_password }}`, and database `{{ tpch_db }}`.
        -   Waits for PostgreSQL to become available.
    5.  **Scaphandre Installation (Energy Monitor)**:
        -   Installs `cargo` and build dependencies.
        -   Clones the Scaphandre repository.
        -   Builds Scaphandre from source and moves the binary to `/usr/local/bin/scaphandre`.
    6.  **Maven Installation**: Installs Apache Maven.
    7.  **Project Builds**:
        -   Builds the `benchbase` module (`./mvnw clean install -P postgres -DskipTests`). As per `CORE-MODULE.md`, BenchBase is used by the `core` module for TPC-H schema creation and data loading.
        -   Builds the `core` module (`mvn clean install -P executable-jar`) to produce a runnable JAR for database initialization.
    8.  **Core Module Configuration**:
        -   Modifies `/root/RestQFramework/core/src/main/resources/application.properties` to configure the database connection (URL, username, password) to point to the local PostgreSQL container.
        -   Rebuilds the `core` module with the updated configuration.
    9.  **Power Monitoring Setup**:
        -   Executes `/root/RestQFramework/ansible-benchmark/INTEL/setup-formula-config.sh`. This script is responsible for setting up a power monitoring solution (likely involving Intel Power Gadget or similar tools) that stores data in a MongoDB container (named `mongodb` by convention, as seen in later data extraction tasks).
    10. **Database Initialization & Data Loading**:
        -   Runs the `core` module\'s executable JAR (`java -jar target/core-1.0-SNAPSHOT.jar`). This executes `InitDB.java` (see `CORE-MODULE.md`), which creates the TPC-H schema and loads data using BenchBase.
    11. **Start Scaphandre Monitoring**:
        -   Starts `scaphandre json` in the background to collect energy consumption data for the DB server node and its containers, saving it to `/root/experiments_summary_dbserver.json`.

### 4.3. Play 3: Setup Node 2 (API Server)
-   **Hosts**: `node2`
-   **Remote User**: `root`
-   **Purpose**: Configures the second node as the API application server.
-   **Tasks**:
    1.  **Java Installation**: Downloads and installs JDK 21.
    2.  **Docker & Build Tools**: Installs Docker, Docker Compose, `cargo`, and Maven (similar to Node 1).
    3.  **Scaphandre Installation**: Builds and installs Scaphandre (similar to Node 1).
    4.  **Repository Clone**: Clones the `RestQFramework` Git repository.
    5.  **Power Monitoring Setup**: Executes `setup-formula-config.sh` for power monitoring on this node.
    6.  **Project Builds**:
        -   Builds `benchbase` module.
        -   Builds the `core` module as a simple JAR (`mvn clean install -P simple-jar`) to be used as a dependency by `api-http`.
    7.  **API Module Configuration**:
        -   Modifies `/root/RestQFramework/api-http/src/main/resources/application.properties` to point `spring.datasource.url` to the PostgreSQL database on Node 1 (`{{ hostvars[\'node1\'].ansible_host }}`).
    8.  **Build API Module**: Builds the `api-http` module (`mvn clean install -P springboot-app`) to produce a runnable Spring Boot JAR. As per `API-MODULE.MD`, this JAR contains the REST API.
    9.  **Start Scaphandre Monitoring**: Starts `scaphandre json` for API server energy data collection, saving to `/root/experiments_summary_apiserver.json`.
    10. **API Server Deployment**:
        -   Copies the built `api-http-1.0-SNAPSHOT.jar` to `/root/RestQFramework/ansible-benchmark/docker-api/target/`.
        -   Updates `/root/RestQFramework/ansible-benchmark/docker-api/docker-compose.yml` with the correct database connection environment variables (URL, username, password) pointing to Node 1.
        -   Starts the API server in a Docker container using `docker-compose up -d` from the `ansible-benchmark/docker-api` directory.
        -   Waits for the API server port (`{{ api_port }}`) to become available.

### 4.4. Play 4: Setup Node 3 (Benchmark Client)
-   **Hosts**: `node3`
-   **Remote User**: `root`
-   **Purpose**: Configures the third node to run the benchmark client.
-   **Tasks**:
    1.  **Java Installation**: Downloads and installs JDK 21.
    2.  **Maven Installation**: Installs Maven.
    3.  **Repository Clone**: Clones the `RestQFramework` Git repository.
    4.  **Project Builds (Dependencies)**:
        -   Builds `benchbase`.
        -   Builds `core` module as a simple JAR. These are likely dependencies for the benchmark tool within `api-http`.
    5.  **Benchmark Configuration**:
        -   Copies `benchmark-config.xml` from the Ansible controller to `/root/RestQFramework/api-http/src/main/resources/benchmark-config.xml` on Node 3. This file dictates the benchmark parameters, endpoints, and experiment configurations as described in `BENCHMARK.md`.
        -   Modifies `ApiBenchmark.java` within the cloned `api-http` source to set `BASE_URL` to Node 2\'s API endpoint (`http://{{ hostvars[\'node2\'].ansible_host }}:{{ api_port }}/api/reports`).
    6.  **Build Benchmark Tool**: Builds the `api-http` module using the `benchmark-app` profile (`mvn clean install -P benchmark-app`). This profile, as per `API-MODULE.MD` and `BENCHMARK.MD`, packages the `ApiBenchmark.java` tool and its dependencies into an executable JAR.
    7.  **Verify API Server**: Waits for the API server on Node 2 to be accessible.
    8.  **Run Benchmark**:
        -   Executes the benchmark JAR (`java -jar target/api-http-1.0-SNAPSHOT-jar-with-dependencies.jar`).
        -   Output is redirected to `/root/benchmark_client.log`. The benchmark tool generates JSON result files (e.g., `benchmark_results_*.json`) in its working directory (`/root/RestQFramework/api-http/`).

### 4.5. Plays 5 & 6: Stopping Scaphandre Measurement
-   **Hosts**: `node1`, `node2` respectively.
-   **Purpose**: Stops the Scaphandre energy monitoring processes.
-   **Tasks**: Uses `pkill -f "scaphandre json ..."` to terminate the Scaphandre processes.

### 4.6. Plays for Results Collection
-   **Purpose**: Fetches all generated data from the remote nodes to the Ansible controller.
-   **Steps**:
    1.  **Fetch Scaphandre Results (Node 1 & 2)**:
        -   Fetches `/root/experiments_summary_dbserver.json` (from Node 1) and `/root/experiments_summary_apiserver.json` (from Node 2) to `/tmp/` on the Ansible controller.
        -   Creates a local directory `~/Desktop/Results_rest_q_xml_benchmarks/experiment_{{ timestamp }}` on the controller.
    2.  **Install MongoDB Tools (Node 1 & 2)**: Installs `mongodb-database-tools` (specifically `mongoexport`) on Node 1 and Node 2.
    3.  **Fetch MongoDB Power Dumps (Node 1 & 2)**:
        -   On Node 1: Executes `docker exec mongodb mongoexport ...` to dump the `power_reports` collection from the `db_power` MongoDB database (running in the `mongodb` container started by `setup-formula-config.sh`). The dump is saved as `mongodump-DB-server.json`.
        -   Fetches this dump to `~/Desktop/Results_rest_q_xml_benchmarks/experiment_{{ timestamp }}/mongodump-DB-server.json`.
        -   Repeats for Node 2, fetching `mongodump-API-server.json`.
    4.  **Fetch API Server Logs (Node 2)**:
        -   Gets logs from the `spring-api` Docker container using `docker logs spring-api`.
        -   Fetches these logs to `~/Desktop/Results_rest_q_xml_benchmarks/experiment_{{ timestamp }}/api_server_app.log`.
    5.  **Fetch Benchmark Client Logs (Node 3)**:
        -   Fetches `/root/benchmark_client.log`.
        -   Fetches `/var/log/syslog` from Node 3.
        -   Logs are saved to `~/Desktop/Results_rest_q_xml_benchmarks/experiment_{{ timestamp }}/`.

### 4.7. Plays for Container ID Collection
-   **Hosts**: `node1`, `node2` respectively.
-   **Purpose**: Retrieves Docker container IDs for the DB and API server containers.
-   **Tasks**:
    1.  On Node 1, get the ID of the `db-docker-container` and store it as fact `db_container_id_fact`.
    2.  On Node 2, get the ID of the `spring-api` container and store it as fact `api_container_id_fact`. These facts are used later by the `JsonCombiner`.

### 4.8. Play: Aggregate Results and Fetch Final Files (on Node 3)
-   **Hosts**: `node3` (acts as a temporary aggregation point)
-   **Purpose**: Combines various JSON results into a single file.
-   **Tasks**:
    1.  **Prepare Aggregation Directory**: Creates `/root/fixed_json_files` on Node 3.
    2.  **Transfer Scaphandre Results to Node 3**: Copies `experiments_summary_dbserver.json` and `experiments_summary_apiserver.json` from the controller\'s `/tmp/` directory *to* Node 3\'s `/root/fixed_json_files/`.
    3.  **Compile `JsonFixer`**: Compiles `com.restq.utils.JsonFixer.java` utility. (Its exact role is not documented here but implies some preprocessing of JSON files).
    4.  **Collect Benchmark Results**: Finds all `benchmark_results_*.json` files (generated by `ApiBenchmark` on Node 3) and copies them into `/root/fixed_json_files/`.
    5.  **Create Container Info JSON**: Creates `container_info.json` in `/root/fixed_json_files/` containing the `db_container_id_fact` (from Node 1) and `api_container_id_fact` (from Node 2). This file is then fetched to the controller.
    6.  **Build and Run `JsonCombiner`**:
        -   Compiles `com.restq.utils.JsonCombiner.java`.
        -   Runs the `JsonCombiner` Java utility. It takes `/root/fixed_json_files` (containing benchmark results, Scaphandre data, and container info) as input and produces `/root/combined_results_{{ timestamp }}.json`. This utility is responsible for creating the final aggregated dataset.
    7.  **Fetch Combined Results**: Fetches the `/root/combined_results_{{ timestamp }}.json` file from Node 3 to the controller at `~/Desktop/Results_rest_q_xml_benchmarks/experiment_{{ timestamp }}/combined_results.json`.

## 5. Outputs and Artifacts

Upon successful completion, the playbook will generate and collect the following artifacts on the Ansible controller machine in the `~/Desktop/Results_rest_q_xml_benchmarks/experiment_{{ timestamp }}/` directory:

-   `experiments_summary_dbserver.json`: Raw Scaphandre energy data for Node 1. (Also copied to Node 3 for combining)
-   `experiments_summary_apiserver.json`: Raw Scaphandre energy data for Node 2. (Also copied to Node 3 for combining)
-   `mongodump-DB-server.json`: Power consumption data for Node 1 from the MongoDB instance.
-   `mongodump-API-server.json`: Power consumption data for Node 2 from the MongoDB instance.
-   `api_server_app.log`: Application logs from the `api-http` Spring Boot application running on Node 2.
-   `benchmark_client.log`: Standard output/error from the `ApiBenchmark` tool running on Node 3.
-   `node3_syslog.log`: System log from Node 3.
-   `container_info.json`: Contains the Docker container IDs for the database and API server.
-   `combined_results.json`: The final aggregated JSON file produced by `JsonCombiner`. This file is expected to merge:
    -   Benchmark results from `ApiBenchmark` (structure detailed in `BENCHMARK.md`, including latencies, throughput per experiment).
    -   Energy data from Scaphandre (`experiments_summary_dbserver.json`, `experiments_summary_apiserver.json`).
    -   Power data from MongoDB dumps (`mongodump-DB-server.json`, `mongodump-API-server.json`).
    -   Container information (`container_info.json`).

## 6. How to Run

1.  Ensure all prerequisites are met (Ansible, Grid\'5000 access, playbook files).
2.  Define necessary extra variables, especially `grid_site`, `timestamp`, and `scaphandre_timestep_s`.
    ```bash
    export TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    export GRID_SITE="your_grid5000_site" # e.g., nancy, rennes, lille
    export SCAPHANDRE_TIMESTEP=1 # Example: 1 second
    ```
3.  Execute the playbook:
    ```bash
    ansible-playbook ansible-benchmark/playbook.yml --extra-vars "grid_site=${GRID_SITE} timestamp=${TIMESTAMP} scaphandre_timestep_s=${SCAPHANDRE_TIMESTEP}"
    ```
    Adjust the path to `playbook.yml` if necessary.

4.  Monitor the execution. Results will be collected in the specified desktop directory on the controller.

## 7. Dependencies on RestQFramework Modules

-   **`core` module (`CORE-MODULE.md`)**:
    -   Used on Node 1 to initialize the TPC-H database schema and load data via its `InitDB` class and BenchBase integration.
    -   Built as a dependency (`simple-jar`) for the `api-http` module on Node 2 and Node 3.
-   **`api-http` module (`API-MODULE.MD`)**:
    -   The main application deployed on Node 2, providing REST endpoints.
    -   Its `ApiBenchmark` tool (built with `benchmark-app` profile) is used on Node 3 to perform the load testing.
    -   Configuration relies on `application.properties` and `benchmark-config.xml`.
-   **`benchbase` module**:
    -   Built as a dependency for the `core` module\'s data loading process.
-   **Utility Classes (`com.restq.utils`)**:
    -   `JsonFixer.java` and `JsonCombiner.java` from the `api-http` module are used on Node 3 for post-processing and aggregating results.

## 8. External Tools and Scripts

-   **Scaphandre**: Used for fine-grained energy monitoring on Node 1 and Node 2.
-   **`ansible-benchmark/INTEL/setup-formula-config.sh`**: A critical script for setting up a separate power monitoring solution that logs to a MongoDB instance. The specifics of this script are not detailed in the playbook but its role is evident from the MongoDB export tasks.
-   **Docker & Docker Compose**: Used to containerize PostgreSQL (Node 1), the API server (Node 2), and the MongoDB instance for power monitoring (Node 1 & 2, via `setup-formula-config.sh`). 