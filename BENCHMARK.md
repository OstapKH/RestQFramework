# Benchmark `api-http` Module 

The `api-http` module includes a built-in benchmarking tool, `ApiBenchmark.java`, designed to test the performance of its exposed HTTP API endpoints. This document outlines how the benchmark works, how to configure it, and what kind of results it produces.

## Overview

The benchmark tool simulates multiple clients sending requests concurrently to the API endpoints defined in a configuration file. It measures response latencies and other metrics to help assess the API's performance under various load conditions.

## Core Components

-   **`ApiBenchmark.java`**: The main executable class that orchestrates the benchmark. It reads the configuration, runs experiments, collects data, and generates results.
-   **`benchmark-config.xml`**: An XML file (located at `api-http/src/main/resources/benchmark-config.xml`) that defines the benchmark parameters, including target endpoints, and various experiment configurations.
-   **Supporting Classes (within `ApiBenchmark.java`)**:
    -   `BenchmarkConfig`, `EndpointConfig`, `ExperimentConfig`, `ProbabilityConfig`: JAXB classes used to parse the `benchmark-config.xml` file.
-   **Output**: The benchmark produces a JSON file (e.g., `benchmark_results_yyyyMMdd_HHmmss.json`) containing detailed results for each experiment and run.

## How it Works

1.  **Configuration Loading**:
    -   The `ApiBenchmark` class starts by parsing the `benchmark-config.xml` file.
    -   This file defines:
        -   A global list of API **endpoints** with unique names and their corresponding URL paths (including query parameters).
            -   **Note**: Currently, the query parameters for these endpoints are fixed within the `benchmark-config.xml`. 
            
            **TODO:** Implement functionality to use variable parameters for more dynamic testing scenarios.
        -   A series of **experiments**, each with a specific configuration.

2.  **Experiment Execution**:
    -   The benchmark iterates through each defined `experiment` in the configuration file.
    -   For each experiment:
        -   It performs a specified number of **runs**.
        -   **Concurrency**: It uses a fixed thread pool to simulate a configured number of concurrent **connections** (clients).
        -   **Request Generation**: For each connection/client:
            -   A dedicated "producer" thread generates requests at a specified **requests-per-second (RPS)** rate.
            -   The producer thread selects an endpoint to call based on the **probabilities** defined for that experiment in the `benchmark-config.xml`.
            -   Requests are placed into a blocking queue unique to that connection.
        -   **Request Execution**:
            -   Each client thread (from the thread pool) consumes requests from its dedicated queue.
            -   It uses Apache HttpClient 5 to send HTTP GET requests to the chosen API endpoint (base URL is `http://localhost:8086/api/reports` by default, concatenated with the endpoint-specific path).
        -   **Duration**: Each run of an experiment continues for a configured **duration** (in seconds).
        -   **Pauses**: Configurable pauses can be set between runs of an experiment and between different experiments.

3.  **Data Collection**:
    -   For every HTTP request sent, the benchmark records the **latency**. Essentially, this is the time elapsed from when the user (simulated by the benchmark tool) makes a request until they receive the complete response. This total round-trip time includes: network travel time to the server, all server-side processing (including database interaction, business logic execution, etc.), and network travel time for the response back to the client. Latencies are timestamped to record when the request was initiated.
    -   It also counts the total number of **successful requests**.

4.  **Results Reporting**:
    -   After all experiments and their runs are completed, the benchmark aggregates all collected data.
    -   It generates a single JSON output file (e.g., `benchmark_results_yyyyMMdd_HHmmss.json`).
    -   This JSON file includes:
        -   Overall benchmark metadata (timestamp, config file path, base URL).
        -   Details of each experiment, including its configuration (connections, RPS, duration, probabilities).
        -   For each run within an experiment:
            -   Start and end timestamps.
            -   Total successful requests.
            -   Achieved throughput (requests per second).
            -   Latency statistics:
                -   Minimum latency
                -   Maximum latency
                -   Median latency
                -   Percentile latencies (e.g., 50th, 90th, 95th, 99th).
            -   A list of all individual timestamped latencies.

## Configuration (`benchmark-config.xml`)

The benchmark is configured via `api-http/src/main/resources/benchmark-config.xml`. Here's an example structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<benchmark-config>
    <!-- Optional: Pause in milliseconds between different experiments -->
    <pauseBetweenExperiments-ms>5000</pauseBetweenExperiments-ms>

    <endpoints>
        <endpoint name="pricing-summary">/pricing-summary?delta=3&amp;shipDate=1998-12-01</endpoint>
        <endpoint name="order-priority-count">/order-priority-count?date=2023-01-01</endpoint>
        <!-- Define other endpoints -->
    </endpoints>

    <experiment>
        <experiment_name>HighLoad_OrderPriority</experiment_name>
        <runs>5</runs> <!-- Number of times to repeat this specific experiment setup -->
        <pause-between-runs-ms>10000</pause-between-runs-ms> <!-- Pause between repetitions of this experiment -->
        <connections>50</connections> <!-- Number of concurrent client connections -->
        <requests-per-second>100</requests-per-second> <!-- Target RPS per connection -->
        <duration-seconds>60</duration-seconds> <!-- Duration of each run in seconds -->
        <probabilities>
            <!-- Probabilities must sum to 1.0 if all listed endpoints are to be hit,
                 or define probabilities for a subset of endpoints. -->
            <probability endpoint="pricing-summary">0.0</probability>
            <probability endpoint="order-priority-count">1.0</probability>
            <!-- Other endpoint probabilities -->
        </probabilities>
    </experiment>

    <!-- Define other experiments -->
</benchmark-config>
```

**Key Configuration Elements:**

-   `<benchmark-config>`: Root element.
    -   `<pauseBetweenExperiments-ms>` (optional): Global pause in milliseconds between the execution of different `<experiment>` blocks.
    -   `<endpoints>`: Contains a list of `<endpoint>` definitions.
        -   `<endpoint name="unique-name">/path?params</endpoint>`: Defines an API endpoint. The `name` is used to reference it in experiment probabilities. The value is the relative URL path and query string.
    -   `<experiment>`: Defines a single benchmark scenario. Multiple `experiment` blocks can exist.
        -   `<experiment_name>`: A descriptive name for the experiment.
        -   `<runs>`: The number of times this specific experiment configuration will be executed.
        -   `<pause-between-runs-ms>`: Pause in milliseconds between each run of this experiment.
        -   `<connections>`: The number of concurrent virtual users (threads) to simulate.
        -   `<requests-per-second>`: The target number of requests each connection will attempt to send per second. The total target RPS for the experiment is `connections * requests-per-second`.
        -   `<duration-seconds>`: The length of time, in seconds, that each run of this experiment will last.
        -   `<probabilities>`: Contains a list of `<probability>` elements.
            -   `<probability endpoint="name-ref">0.75</probability>`: Assigns a probability (0.0 to 1.0) to the endpoint referenced by `name-ref`. For balanced selection, the sum of probabilities for targeted endpoints should be 1.0. If an endpoint is not listed or has a probability of 0, it won't be called in that experiment.

## Running the Benchmark

As per `API-MODULE.md`:

1.  **Build**: Build the `api-http` module using Maven. The default profile or the `benchmark-app` profile should produce the necessary JAR with dependencies.
    ```bash
    # Example:
    mvn clean package -Pbenchmark-app 
    # or
    mvn clean package
    ```
2.  **Execute**: Run the `ApiBenchmark` main class from the generated JAR.
    ```bash
    java -jar api-http-<version>-jar-with-dependencies.jar 
    ```
    (The exact JAR name depends on the Maven build configuration.)

The `ApiBenchmark` class is in the `com.restq.api_http.Benchmark` package. If running from an IDE or a non-packaged setup, ensure the classpath is correctly set and execute `com.restq.api_http.Benchmark.ApiBenchmark`.

## Output Analysis

The primary output is the timestamped JSON file (e.g., `benchmark_results_20231027_103000.json`). This file can be parsed and analyzed to:
-   Compare performance across different experiments (e.g., how latency changes with increased connections or RPS).
-   Identify bottlenecks by observing high latencies for specific endpoints or configurations.
-   Understand the distribution of latencies (min, max, median, percentiles).
-   Verify if the target throughput (RPS) is being met.

The raw list of all timestamped latencies for each run provides granular data for more detailed analysis if required.

## JSON Output File Structure

The benchmark tool (`ApiBenchmark.java`) produces a JSON output. In practice, this output is found nested within a larger JSON structure, under a key such as `"benchmark_results"`. This encompassing JSON structure also includes other data from different tools, as observed with keys like `"api_server_energy"`, `"db_server_energy"`, and `"container_info"` in the provided example.

The following describes the structure of the JSON object generated by `ApiBenchmark.java` (i.e., the content of the `"benchmark_results"`):

```json
{
  "endpoints": { // Object mapping configured endpoint names to their URL paths
    "endpoint_name_1": "string_url_path_1",
    "endpoint_name_2": "string_url_path_2"
    // ... all configured endpoints
  },
  "global_config": { // Contains some global configuration values
    "pauseBetweenExperiments_ms": long
  },
  "pauseBetweenExperiments_ms": long, // Global pause value from config (repeated from global_config)
  "experiments": { // Object containing results for all executed experiments
    "experiment_name_1_from_config": {
      "duration_seconds": int, // Configured duration per run for this experiment
      "requests_per_second": int, // Configured target RPS per connection
      "pause_between_runs_ms": long, // Configured pause between runs for this experiment
      "runs_configured": int, // Number of runs specified in config
      "probabilities": { // Endpoint selection probabilities for this experiment
        "endpoint_name_1": double_probability,
        "endpoint_name_2": double_probability
        // ... probabilities for this experiment
      },
      "runs": [ // Array of results, one object per run executed for this experiment
        {
          "experiment_name": "string_experiment_name", // Name of the experiment (often repeats the parent key)
          "start_timestamp": long, // System.currentTimeMillis() at the start of this specific run
          "latencies": [ // Array of all individual latency records for this run
            {
              "latency_ns": long, // Measured latency for this specific request in nanoseconds
              "timestamp": long // Timestamp when this specific request was made (milliseconds)
            }
            // ... more individual latency objects, sorted by timestamp
          ]
        }
        // ... more run objects if runs_configured > 1
      ]
    },
    "experiment_name_2_from_config": {
      // ... structure repeats for other experiments
    }
  }
  // Note: The top-level timestamp and config_file path for the ApiBenchmark output
  // (previously documented as "timestamp" and "config_file" at the root of ApiBenchmark's own output)
  // might be part of the encompassing JSON structure if this output is embedded.
}
```

**Key characteristics of the `benchmark_results` structure:**

*   **`experiments` object**: Each key is an experiment name from `benchmark-config.xml`.
    *   Each experiment object contains its specific configuration and an array called `runs`.
*   **`runs` array**: Contains one object for each repetition (run) of that experiment.
    *   Each run object in the provided example primarily contains:
        *   `experiment_name`: The name of the experiment.
        *   `start_timestamp`: The start time of the run.
        *   `latencies`: An array of individual request latencies.
            *   Each entry has `latency_ns` (latency in nanoseconds) and `timestamp` (request initiation time in milliseconds).
*   **Aggregated Run Statistics**: The `results_example.json` shows a `run` object that does not include several aggregated statistics which `ApiBenchmark.java` is designed to compute and add. These include:
    *   End timestamp of the run.
    *   Actual duration of the run.
    *   Total successful requests for the run.
    *   Achieved RPS (requests per second) for the run.
    *   An aggregated `latency_ns` object with min, max, median, and percentile latencies for the run.
    The actual output from `ApiBenchmark.java` can contain these additional fields within each run object. Inspect the generated JSON file for the complete set of data produced in a specific execution.
}
```

