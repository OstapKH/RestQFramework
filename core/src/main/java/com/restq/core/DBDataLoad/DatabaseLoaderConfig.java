package com.restq.core.DBDataLoad;

import com.oltpbenchmark.WorkloadConfiguration;
import com.oltpbenchmark.api.LoaderThread;
import com.oltpbenchmark.benchmarks.tpch.TPCHBenchmark;
import com.oltpbenchmark.benchmarks.tpch.TPCHLoader;
import com.oltpbenchmark.types.DatabaseType;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;

@Order(0)
@Configuration
@Slf4j
public class DatabaseLoaderConfig {

    @Value("${spring.datasource.url}")
    private String dbUrl;

    @Value("${spring.datasource.username}")
    private String dbUsername;

    @Value("${spring.datasource.password}")
    private String dbPassword;

    @Value("${app.database.load-sample-data:false}")
    private boolean loadSampleData;

    @Value("${app.database.scale-factor:0.1}")
    private double scaleFactor;

    @Value("${app.database.batch-size:1000}")
    private int batchSize;

    @Value("${app.database.terminals:1}")
    private int terminals;

    private final LocalContainerEntityManagerFactoryBean entityManagerFactory;

    public DatabaseLoaderConfig(LocalContainerEntityManagerFactoryBean entityManagerFactory) {
        this.entityManagerFactory = entityManagerFactory;
    }

    @Bean
    @Order(1)
    public CommandLineRunner databaseLoader(DataSource dataSource) {
        return args -> {
            if (!loadSampleData) {
                log.info("Sample data loading is disabled");
                return;
            }

            try (Connection conn = dataSource.getConnection()) {
                if (isDatabasePopulated(conn)) {
                    log.info("Database is already populated with sample data");
                    return;
                }

                // Create WorkloadConfiguration
                WorkloadConfiguration workConf = new WorkloadConfiguration();
                workConf.setUrl(dbUrl);
                workConf.setUsername(dbUsername);
                workConf.setPassword(dbPassword);
                workConf.setScaleFactor(scaleFactor);
                workConf.setBatchSize(batchSize);
                workConf.setTerminals(terminals);

                // Set database type based on JDBC URL
                DatabaseType dbType = determineDatabaseType(dbUrl);
                workConf.setDatabaseType(dbType);

                log.info("Initializing DB with scale factor: {}", scaleFactor);

                // Create TPCHBenchmark instance with the configuration
                TPCHBenchmark benchmark = new TPCHBenchmark(workConf);

                // First create the database schema - this will initialize the catalog
                log.info("Creating database schema...");
                benchmark.createDatabase();

                // Refresh the catalog to ensure it's initialized
                log.info("Refreshing catalog...");
                benchmark.refreshCatalog();

                // Now that catalog is initialized, we can create the loader
                log.info("Starting data loading process...");
                TPCHLoader loader = new TPCHLoader(benchmark);
                List<LoaderThread> loaderThreads = loader.createLoaderThreads();

                // Run loader threads
                for (LoaderThread thread : loaderThreads) {
                    thread.run();
                }

                log.info("Successfully loaded sample data into database");

            } catch (Exception e) {
                log.error("Failed to load sample data into database", e);
                throw new RuntimeException("Database initialization failed", e);
            }
        };
    }

    private boolean isDatabasePopulated(Connection conn) {
        try (Statement stmt = conn.createStatement()) {
            // Check if CUSTOMER table has any records
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM CUSTOMER");
            rs.next();
            return rs.getInt(1) > 0;
        } catch (Exception e) {
            // If table doesn't exist or other error, we assume database is not populated
            return false;
        }
    }

    private DatabaseType determineDatabaseType(String jdbcUrl) {
        jdbcUrl = jdbcUrl.toLowerCase();
        if (jdbcUrl.contains("postgresql")) {
            return DatabaseType.POSTGRES;
        } else if (jdbcUrl.contains("mysql")) {
            return DatabaseType.MYSQL;
        } else if (jdbcUrl.contains("sqlserver")) {
            return DatabaseType.SQLSERVER;
        } else if (jdbcUrl.contains("oracle")) {
            return DatabaseType.ORACLE;
        } else {
            throw new IllegalArgumentException("Unsupported database type in JDBC URL: " + jdbcUrl);
        }
    }
}