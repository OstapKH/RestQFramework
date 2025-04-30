# RestQFramework API-HTTP Module (`api-http`)

## Overview

The `api-http` module provides the primary HTTP interface for the RestQFramework. It functions as a web application layer, building upon the `core` module. Its primary objective is to expose RESTful endpoints, enabling users or external services to query the TPC-H data managed by the `core` module. This module utilizes the Spring Boot framework for web functionalities, data access (via Spring Data JPA, reusing entities from `core`), input validation, and configuration management.

One of the characteristic of this module is the incorporation of a dedicated API benchmarking tool (`ApiBenchmark`) and associated components, facilitating performance evaluation of the exposed endpoints.

## Project Configuration (`pom.xml`)

Key aspects of the Maven configuration include:

- **Coordinates:** `com.restq:api-http:1.0-SNAPSHOT`
- **Java Version:** 21
- **Core Dependency:** Explicitly depends on `com.restq:core:1.0-SNAPSHOT`.
- **Key Libraries & Technologies:**
    - Spring Boot Starters: `web`, `data-jpa`, `validation`
    - Jackson (JSON Processing)
    - PostgreSQL Driver
    - Apache HttpClient5 (HTTP Client operations)
    - JAXB (XML Binding)
    - JFreeChart (Chart generation; specific usage details require code inspection)
    - JUnit (Testing)
- **Build Configuration:**
    - Managed by Maven, targeting Java 21.
    - Supports building a standard executable Spring Boot web application JAR via the `springboot-app` profile (`mvn package -Pspringboot-app`).
    - Alternatively, produces a JAR with dependencies tailored for executing the API benchmark tool (`ApiBenchmark`), achievable through the default build or the `benchmark-app` profile (`mvn package`).

## Package Structure and Key Components

The primary application code is located within the `com.restq` package, with module-specific components organized under `com.restq.api_http`.

- **`com.restq.APIApplication.java`**: Serves as the main entry point (`@SpringBootApplication`) for initiating the web API.

- **`com.restq.api_http`**: Houses the core logic for the API layer.
    - **`Controllers`**: Defines the HTTP endpoints using Spring MVC annotations (`@RestController`, `@RequestMapping`, `@GetMapping`).
        - `Controller.java`: Functions as the central controller defining endpoints that correspond to specific TPC-H benchmark queries. Each `@GetMapping` method typically accepts query parameters (`@RequestParam`) needed for a TPC-H query (like dates, regions, market segments, brands) and returns a specific DTO containing the query results.
            *Example Endpoint:*
            ```java
            @GetMapping("/pricing-summary") // Corresponds to TPC-H Query 1
            public List<PricingSummaryReport> getPricingSummary(
                @RequestParam(value = "delta", required = false) Integer delta, 
                @RequestParam(value = "shipDate", defaultValue = "1998-12-01") LocalDate shipDate) {
                // ... calls lineItemRepository.getPricingSummaryReport ...
            }
            ```
        - `RequestLoggingInterceptor.java`: Implements a Spring interceptor for logging details of incoming HTTP requests.
    - **`Repositories`**: Contains Spring Data JPA repository interfaces (e.g., `CustomerRepository`, `LineItemRepository`, `OrderRepository`) extending `JpaRepository` or similar. These interfaces are the data access layer, interacting with the entities defined in the `core` module. They contain numerous custom query methods, often defined using the `@Query` annotation or derived from method names, which encapsulate the JPQL or native SQL logic required to execute the specific TPC-H benchmark queries against the database.
        *Example:* `LineItemRepository` provides methods to query the `LineItem` entity, including complex aggregations needed for reports like the Pricing Summary (TPC-H Query 1) or Revenue Increase calculation (TPC-H Query 6).
    - **`DTO` (Data Transfer Objects)**: Represents Plain Old Java Objects (POJOs) specifically designed for the API's request and response data structures. They define the shape of the data returned by the API endpoints, effectively representing the results of the executed TPC-H queries. Using DTOs decouples the API's external contract from the internal database entity structure.
        *Examples:* 
          - `PricingSummaryReport`: Contains fields representing the aggregated results for TPC-H Query 1.
          - `OrderPriorityCountInfo`: Holds the counts for TPC-H Query 4.
          - `MarketShareReport`: Structures the market share percentage data for TPC-H Query 8.
          - `ReturnedItemReport`: Formats the results for TPC-H Query 10.
    - **`Benchmark`**: Encompasses code dedicated to API performance testing.
        - `ApiBenchmark.java`: The main executable class for conducting benchmark tests against the API endpoints, configured through `benchmark-config.xml`.
        - `BenchmarkResult.java`, `Config.java`, `LatencyDistribution.java`: Supporting classes involved in benchmark execution orchestration, configuration handling, and results analysis.
    - **`WebConfig.java`**: A Spring `@Configuration` class for web-tier settings, such as the registration of the `RequestLoggingInterceptor`.

- **`com.restq.utils`**: A designated package for shared utility classes.

## Functionality

The `api-http` module delivers the following capabilities:

1.  **HTTP API Provision:** Exposes REST endpoints (defined in `Controller.java`) enabling queries against TPC-H data.
2.  **Complex Query Execution:** Executes sophisticated database queries via custom methods within its `Repositories`, utilizing the `core` module's entities.
3.  **Data Transformation:** Performs mapping of results from JPA entities to specific Data Transfer Objects (DTOs) for API responses.
4.  **Request Processing:** Uses Spring Boot Web for handling HTTP requests, responses, input validation, and JSON serialization/deserialization.
5.  **API Benchmarking:** Incorporates a utility (`ApiBenchmark`) for measuring the performance characteristics of its own API endpoints.
6.  **Configuration Management:** Configuration is primarily managed via Spring Boot's `application.properties`, augmented by `benchmark-config.xml` and `config.json` for specialized features. (Explained in documentation of a benchmark module)

## Default Configuration (`src/main/resources/application.properties`)

Key default configuration parameters specified in `application.properties` include:

- **Server Port:** Configured to run on port `8086` (`server.port=8086`).
- **Database Connection:** Specifies connection parameters for the PostgreSQL database (`tpchdb` on localhost), mirroring the `core` module's settings (`admin`/`password`).
- **Connection Pooling (Hikari):** Explicitly configures pool parameters (`maximum-pool-size=100`, `minimum-idle=1`).
- **JPA/Hibernate Settings:** Inherits `ddl-auto=none` and `PostgreSQLDialect`. Enables detailed SQL logging (`show-sql=true`, `format_sql=true`) and parameter binding tracing (`logging.level.org.hibernate.SQL=DEBUG`, `logging.level.org.hibernate.type.descriptor.sql.BasicBinder=TRACE`).

These default settings are subject to override through standard Spring Boot configuration mechanisms.

## Execution Instructions

- **API Server Deployment:** Build using the `springboot-app` profile (`mvn clean package -Pspringboot-app`). Execute the generated JAR: `java -jar api-http-<version>.jar`.
- **Benchmark Tool Execution:** Build using the default profile or `benchmark-app` profile (`mvn clean package`). Execute the JAR containing dependencies: `java -jar api-http-<version>-jar-with-dependencies.jar`. Command-line arguments may be required based on the `ApiBenchmark` implementation and the contents of `benchmark-config.xml`.
