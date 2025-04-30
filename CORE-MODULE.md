# RestQFramework Core Module (`core`)

## Overview

The `core` module forms the backbone of the RestQFramework. It handles the essential tasks of database interaction, data modeling, and optionally loading TPC-H benchmark data, all designed primarily for a PostgreSQL database. It uses familiar tools from the Spring ecosystem, like Spring Data JPA with Hibernate handling the persistence details.

## Project Configuration (`pom.xml`)

Here's a quick look at the Maven setup:

- **Coordinates:** `com.restq:core:1.0-SNAPSHOT`
- **Java Version:** 21
- **Key Libraries:**
    - Spring Boot (Data JPA, Web)
    - Hibernate (JPA Implementation)
    - PostgreSQL Driver
    - Lombok
    - BenchBase (TPC-H Benchmarking for PostgreSQL)
    - JUnit
- **Build:** Managed by Maven. It includes profiles to build either a simple JAR or a runnable Spring Boot application JAR. It's also set up to generate Javadoc and test reports (Surefire).

## Package Structure and Key Components

The main code lives under the `com.restq` package.

### `com.restq`

- **`InitDB.java`**:
    - **What it does**: This is the main starting point for setting up and filling the database with TPC-H data. It's a standard Spring Boot application launcher.
    - **How it works**: Running `InitDB` starts the Spring application. Spring finds all the configured components, including `DatabaseLoaderConfig`. Once Spring is ready, it automatically runs a `CommandLineRunner` bean defined in `DatabaseLoaderConfig`. This runner checks if the database needs data and, if so, uses the BenchBase library (`TPCHBenchmark` and `TPCHLoader`) to create the TPC-H schema and load data according to settings like the scale factor.
    - **How to run it**:
        1.  **Executable JAR**: Build the project with the `executable-jar` profile (`mvn package -Pexecutable-jar`) and run the JAR: `java -jar core-<version>-exec.jar`.
        2.  **Configuration**: You control the data loading using application properties (in `application.properties`, environment variables, etc.):
            - `app.database.load-sample-data`: Set to `true` to load data (default is `true` based on the properties file).
            - `spring.datasource.*`: Standard Spring properties for DB URL, username, password.
            - `app.database.scale-factor`: TPC-H size (e.g., 0.1, 1.0, default is 1).
            - `app.database.batch-size`: BenchBase loading batch size (default 1000).
            - `app.database.terminals`: How many loader threads BenchBase uses (default 1).

### `com.restq.core`

This package holds the main logic.

- **`com.restq.core.Models`**:
    - This package contains the Java classes (JPA Entities with `@Entity`) that represent the database tables. The structure mirrors the TPC-H benchmark schema.
        - **`Region`**: Represents geographical regions. A region can contain multiple nations.
          ```java
          @Entity
          @Table(name = "REGION")
          public class Region {
              @Id
              @Column(name = "R_REGIONKEY")
              private Integer regionKey;
              
              @Column(name = "R_NAME")
              private String name;
              
              @OneToMany(mappedBy = "region")
              private List<Nation> nations;
              // ... other fields, getters, setters
          }
          ```
        - **`Nation`**: Represents nations. Each nation belongs to a single region (`@ManyToOne`) and can have many associated customers and suppliers (`@OneToMany`).
          ```java
          @Entity
          @Table(name = "NATION")
          public class Nation {
              @Id
              @Column(name = "N_NATIONKEY")
              private Integer nationKey;
              
              @Column(name = "N_NAME")
              private String name;
              
              @ManyToOne
              @JoinColumn(name = "N_REGIONKEY")
              private Region region;
              
              @OneToMany(mappedBy = "nation")
              private List<Customer> customers;
              
              @OneToMany(mappedBy = "nation")
              private List<Supplier> suppliers;
              // ... other fields, getters, setters
          }
          ```
        - **`Customer`**: Represents customers. Each customer belongs to a single nation (`@ManyToOne`).
          ```java
          @Entity
          @Table(name = "CUSTOMER")
          public class Customer {
              @Id
              @Column(name = "C_CUSTKEY")
              private Integer customerKey;
              
              @Column(name = "C_NAME")
              private String name;
              
              @ManyToOne
              @JoinColumn(name = "C_NATIONKEY")
              private Nation nation;
              // ... other fields (address, phone, acctbal, mktsegment), getters, setters
          }
          ```
        - **`Supplier`**: Represents suppliers. Each supplier belongs to a single nation (`@ManyToOne`).
          ```java
          @Entity
          @Table(name = "SUPPLIER")
          public class Supplier {
              @Id
              @Column(name = "S_SUPPKEY")
              private Integer supplierKey;
              
              @Column(name = "S_NAME")
              private String name;
              
              @ManyToOne
              @JoinColumn(name = "S_NATIONKEY")
              private Nation nation;
              // ... other fields (address, phone, acctbal), getters, setters
          }
          ```
        - **`Part`**: Represents parts. While not directly linked to other entities here, it connects through the `PartSupp` table.
          ```java
          @Entity
          @Table(name = "PART")
          public class Part {
              @Id
              @Column(name = "P_PARTKEY")
              private Integer partKey;
              
              @Column(name = "P_NAME")
              private String name;
              // ... other fields (mfgr, brand, type, size, container, retailprice), getters, setters
          }
          ```
        - **`PartSupp`**: Defines the many-to-many link between parts and suppliers, including stock levels and costs. It uses a composite key (`PartSuppId`) embedded in the entity (`@EmbeddedId`), linking back to `Part` and `Supplier` via `@ManyToOne` and `@MapsId`.
          ```java
          @Embeddable
          public class PartSuppId implements Serializable { // Composite Key
              @Column(name = "PS_PARTKEY") private Integer partKey;
              @Column(name = "PS_SUPPKEY") private Integer supplierKey;
              // equals, hashCode, getters, setters
          }

          @Entity
          @Table(name = "PARTSUPP")
          public class PartSupp {
              @EmbeddedId
              private PartSuppId id;
              
              @ManyToOne @MapsId("partKey")
              @JoinColumn(name = "PS_PARTKEY")
              private Part part;
              
              @ManyToOne @MapsId("supplierKey")
              @JoinColumn(name = "PS_SUPPKEY")
              private Supplier supplier;
              
              @Column(name = "PS_AVAILQTY")
              private Integer availableQuantity;
              
              @Column(name = "PS_SUPPLYCOST")
              private BigDecimal supplyCost;
              // ... comment field, getters, setters
          }
          ```
        - **`Order`**: Represents customer orders. Each order is associated with a single customer (`@ManyToOne`).
          ```java
          @Entity
          @Table(name = "ORDERS") // Note: Class name is Order, table is ORDERS
          public class Order {
              @Id
              @Column(name = "O_ORDERKEY")
              private Integer orderKey;
              
              @ManyToOne
              @JoinColumn(name = "O_CUSTKEY")
              private Customer customer;
              
              @Column(name = "O_ORDERSTATUS")
              private String orderStatus;
              
              @Column(name = "O_TOTALPRICE")
              private BigDecimal totalPrice;
              
              @Column(name = "O_ORDERDATE")
              private LocalDate orderDate;
              // ... other fields (orderpriority, clerk, shippriority), getters, setters
          }
          ```
        - **`LineItem`**: Represents the individual items within an order. It uses a composite key (`LineItemId` - orderKey and lineNumber) via `@EmbeddedId`. Although it holds keys for the order, part, and supplier (`L_ORDERKEY`, `L_PARTKEY`, `L_SUPPKEY`), it doesn't use direct `@ManyToOne` JPA links here. Queries typically join using these key values manually.
          ```java
          @Embeddable
          public class LineItemId implements Serializable { // Composite Key
              @Column(name = "L_ORDERKEY") private Integer orderKey;
              @Column(name = "L_LINENUMBER") private Integer lineNumber;
              // equals, hashCode, getters, setters
          }
          
          @Entity
          @Table(name = "LINEITEM")
          public class LineItem {
              @EmbeddedId
              private LineItemId id; // Contains orderKey and lineNumber

              // NOTE: While orderKey is part of the ID, there's no direct @ManyToOne Order here.
              //       Joins would typically be done via orderKey.
              //       Similarly, partKey and suppKey are present but not direct relationships.
              @Column(name = "L_PARTKEY") private Integer partKey;
              @Column(name = "L_SUPPKEY") private Integer suppKey;
              
              @Column(name = "L_QUANTITY") private BigDecimal quantity;
              @Column(name = "L_EXTENDEDPRICE") private BigDecimal extendedPrice;
              // ... other fields (discount, tax, dates, flags, status, etc.), getters, setters
          }
          ```
- **`com.restq.core.DBDataLoad`**:
    - **`DatabaseLoaderConfig.java`**: This Spring configuration (`@Configuration`) class sets up and runs the TPC-H data loading process when the application starts.
        - It defines a `CommandLineRunner` bean, which Spring executes automatically once the application context is ready.
        - **Loading Check**: Before doing anything, it checks if the `app.database.load-sample-data` property is `true` and if the database looks empty (by checking the `CUSTOMER` table). This stops it from accidentally reloading data.
        - **Configuration**: It reads database connection details (`spring.datasource.*`) and TPC-H settings (`app.database.*`) like scale factor from the Spring environment (e.g., `application.properties`).
        - **BenchBase Usage**: It uses BenchBase to handle the TPC-H specifics:
            - Configures BenchBase's `WorkloadConfiguration` with the database details and TPC-H settings.
            - Figures out the database type (like `POSTGRES`) from the JDBC URL.
            - Uses `TPCHBenchmark` to create the database schema (`benchmark.createDatabase()`) and refresh BenchBase's view of the database (`benchmark.refreshCatalog()`).
            - Uses `TPCHLoader` to get loader threads and runs them (`thread.run()`) to insert the TPC-H data.
        - **Error Logging**: Logs any errors encountered during the loading process.

## Functionality

In short, the `core` module handles:

1.  **Data Persistence:** Defining the database structure through JPA entities (`Models`) and enabling data operations.
2.  **Database Schema:** Providing the classes that map to a TPC-H benchmark schema in PostgreSQL.
3.  **Data Loading:** Optionally populating the database with TPC-H data using BenchBase, configured via `DatabaseLoaderConfig`.
4.  **Database Initialization:** Providing the `InitDB` class to kick off the schema creation and data loading process.

## Usage

Other modules in the RestQFramework rely on `core` when they need to interact with the database, work with the TPC-H entities, or trigger the data loading. It lays the data groundwork for the rest of the framework.

## Default Configuration (`src/main/resources/application.properties`)

The project ships with some default settings in `application.properties`:

- **Database:** Points to a local PostgreSQL instance (`jdbc:postgresql://localhost:5432/tpchdb`) using `admin`/`password` credentials.
- **JPA/Hibernate:**
    - Doesn't automatically change the database schema (`ddl-auto=none`); schema creation is handled by the `DatabaseLoaderConfig`.
    - Configured for PostgreSQL (`PostgreSQLDialect`).
    - Set to log SQL statements (`show-sql=true`, `format_sql=true`).
- **Data Loading:**
    - Turned on by default (`app.database.load-sample-data=true`).
    - Default TPC-H scale factor: `1` (`app.database.scale-factor=1`).
    - Default loading batch size: `1000` (`app.database.batch-size=1000`).
    - Default loader threads: `1` (`app.database.terminals=1`).

Remember, you can override these defaults using standard Spring Boot methods (environment variables, command-line options, etc.).
