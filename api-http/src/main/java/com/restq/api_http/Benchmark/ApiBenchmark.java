package com.restq.api_http.Benchmark;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.Collectors;

import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBException;
import jakarta.xml.bind.Unmarshaller;
import jakarta.xml.bind.annotation.*;

import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.NoHttpResponseException;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.EntityDetails;
import org.apache.hc.core5.http.HttpRequest;
import org.apache.hc.core5.http.protocol.HttpContext;

import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartUtils;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.data.statistics.HistogramDataset;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

public class ApiBenchmark {

    private static final Logger logger = LoggerFactory.getLogger(ApiBenchmark.class);

    // Update to use XML config file
    private static final String CONFIG_FILE = "src/main/resources/benchmark-config.xml";
    private static final String BASE_URL = "http://localhost:8086/api/reports";
    private static Map<String, String> ENDPOINTS;

    private static final Random random = new Random();

    // Map to track the initial port used by each thread
    private static final ConcurrentMap<String, Integer> initialPortMap = new ConcurrentHashMap<>();

    // Global JSON result object to store all experiment results
    private static ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
    private static ObjectNode allResults;
    private static String resultFileName;

    public static void main(String[] args) throws IOException, InterruptedException {
        try {
            // Initialize global result variables
            allResults = mapper.createObjectNode();
            // Generate a timestamped file name for all results
            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
            resultFileName = "benchmark_results_" + timestamp + ".json";
            
            // Load XML configuration
            File configFile = new File(CONFIG_FILE);
            JAXBContext context = JAXBContext.newInstance(BenchmarkConfig.class);
            Unmarshaller unmarshaller = context.createUnmarshaller();
            BenchmarkConfig benchmarkConfig = (BenchmarkConfig) unmarshaller.unmarshal(configFile);
            
            // Add metadata to results
            allResults.put("timestamp", timestamp);
            allResults.put("config_file", CONFIG_FILE);
            allResults.put("base_url", BASE_URL);
            allResults.put("pauseBetweenExperiments_ms", benchmarkConfig.getPauseBetweenExperiments());
            
            // Add endpoints configuration
            ObjectNode endpointsNode = allResults.putObject("endpoints");
            for (EndpointConfig endpoint : benchmarkConfig.getEndpoints()) {
                endpointsNode.put(endpoint.getName(), endpoint.getUrl());
            }
            
            // Set up endpoint mappings
            ENDPOINTS = new HashMap<>();
            for (EndpointConfig endpoint : benchmarkConfig.getEndpoints()) {
                ENDPOINTS.put(endpoint.getName(), endpoint.getUrl());
            }
            
            // Add global configuration section
            ObjectNode globalConfigNode = allResults.putObject("global_config");
            globalConfigNode.put("pauseBetweenExperiments_ms", benchmarkConfig.getPauseBetweenExperiments());
            
            // Add experiments container
            ObjectNode experimentsNode = allResults.putObject("experiments");
            
            // Run each experiment
            for (ExperimentConfig experiment : benchmarkConfig.getExperiments()) {
                logger.info("Starting experiment: {}", experiment.getExperimentName());
                
                // Create a node for this experiment
                ObjectNode experimentNode = experimentsNode.putObject(experiment.getExperimentName());
                experimentNode.put("runs_configured", experiment.getRuns());
                experimentNode.put("connections", experiment.getConnections());
                experimentNode.put("requests_per_second", experiment.getRequestsPerSecond());
                experimentNode.put("duration_seconds", experiment.getDuration());
                experimentNode.put("pause_between_runs_ms", experiment.getPauseBetweenRuns());
                
                // Add probabilities to experiment config
                ObjectNode expProbNode = experimentNode.putObject("probabilities");
                for (Map.Entry<String, Double> entry : experiment.getProbabilitiesMap().entrySet()) {
                    expProbNode.put(entry.getKey(), entry.getValue());
                }
                
                // Add runs array to this experiment
                ArrayNode runsArray = experimentNode.putArray("runs");
                
                runExperiment(experiment, benchmarkConfig, runsArray);
                
                // Pause between experiments if there are more to run
                if (benchmarkConfig.getExperiments().indexOf(experiment) < benchmarkConfig.getExperiments().size() - 1) {
                    logger.info("Pausing for {} ms before next experiment", benchmarkConfig.getPauseBetweenExperiments());
                    Thread.sleep(benchmarkConfig.getPauseBetweenExperiments());
                }
            }
            
            // Write all results to a single file
            mapper.writeValue(new File(resultFileName), allResults);
            logger.info("All experiments completed. Results saved to {}", resultFileName);
            
        } catch (JAXBException e) {
            logger.error("Error parsing XML configuration: {}", e.getMessage(), e);
        }
    }
    
    private static void runExperiment(ExperimentConfig experiment, BenchmarkConfig benchmarkConfig, ArrayNode runsArray) throws InterruptedException, IOException {
        for (int run = 0; run < experiment.getRuns(); run++) {
            logger.info("Starting run {} of {} for experiment {}", run + 1, experiment.getRuns(), experiment.getExperimentName());
            
            // Clear initial port map for each run
            initialPortMap.clear();

            ExecutorService executor = Executors.newFixedThreadPool(experiment.getConnections());
            List<Future<ClientTaskResult>> futures = new ArrayList<>();
            List<TimestampedLatency> allLatencies = new ArrayList<>();

            // Create a queue for each thread
            List<BlockingQueue<String>> queues = new ArrayList<>();
            for (int i = 0; i < experiment.getConnections(); i++) {
                queues.add(new LinkedBlockingQueue<>());
            }

            long startTimestamp = System.currentTimeMillis();
            long endTimestamp = startTimestamp + experiment.getDuration() * 1000;

            // Start producer thread to add requests to queues
            Thread producerThread = new Thread(() -> {
                try {
                    while (System.currentTimeMillis() < endTimestamp) {
                        long startTime = System.currentTimeMillis();
                        String endpoint = chooseEndpoint(experiment.getProbabilitiesMap());

                        for (BlockingQueue<String> queue : queues) {
                            for (int j = 0; j < experiment.getRequestsPerSecond(); j++) {
                                queue.put(endpoint);
                            }
                        }

                        long elapsedTime = System.currentTimeMillis() - startTime;
                        if (elapsedTime < 1000) {
                            Thread.sleep(1000 - elapsedTime);
                        } else {
                            logger.warn("Warning: Adding requests took longer than 1 second.");
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
            producerThread.start();

            // Start client tasks
            for (int i = 0; i < experiment.getConnections(); i++) {
                futures.add(executor.submit(new ClientTask(experiment, queues.get(i), endTimestamp)));
            }

            producerThread.join();

            int totalSuccessfulRequests = 0;
            for (Future<ClientTaskResult> future : futures) {
                try {
                    ClientTaskResult result = future.get();
                    allLatencies.addAll(result.getLatencies());
                    totalSuccessfulRequests += result.getSuccessfulRequests();
                } catch (ExecutionException | InterruptedException e) {
                    logger.error("Error in executing client task: {}", e.getMessage(), e);
                }
            }

            // Sort all latencies by timestamp to maintain chronological order
            allLatencies.sort(Comparator.comparing(TimestampedLatency::getTimestamp));

            // Extract just the latency values for calculations (in chronological order)
            List<Long> orderedLatencyValues = allLatencies.stream()
                .map(TimestampedLatency::getLatency)
                .collect(Collectors.toList());

            executor.shutdown();
            executor.awaitTermination(2, TimeUnit.SECONDS);

            long actualEndTimestamp = System.currentTimeMillis();

            // Pass the ordered latencies to the results
            addRunResults(startTimestamp, actualEndTimestamp, orderedLatencyValues, allLatencies,
                    totalSuccessfulRequests, experiment.getConnections(), run, experiment, runsArray);

            // Create latency distributions but don't save images
            createLatencyHistogram(orderedLatencyValues, experiment.getExperimentName() + "_run" + run);
            createLatencyCDF(orderedLatencyValues, experiment.getExperimentName() + "_run" + run);

            // Pause between runs if there are more to run
            if (run < experiment.getRuns() - 1) {
                logger.info("Pausing for {} ms before next run", experiment.getPauseBetweenRuns());
                Thread.sleep(experiment.getPauseBetweenRuns());
            }
        }
    }

    private static class ClientTask implements Callable<ClientTaskResult> {
        private final ExperimentConfig experiment;
        private final CloseableHttpClient httpClient;
        private final BlockingQueue<String> queue;
        private final long endTimestamp;
        private int successfulRequests = 0; // Track successful requests
        private final String threadName;

        public ClientTask(ExperimentConfig experiment, BlockingQueue<String> queue, long endTimestamp) {
            this.experiment = experiment;
            this.queue = queue;
            this.endTimestamp = endTimestamp;
            this.threadName = Thread.currentThread().getName();

            this.httpClient = HttpClients.custom()
                    .addRequestInterceptorFirst((HttpRequest request, EntityDetails entity, HttpContext context) -> {
                        initialPortMap.computeIfAbsent(threadName, k -> 0);
                    })
                    .setConnectionReuseStrategy((request, response, context) -> true)
                    .build();
        }

        @Override
        public ClientTaskResult call() {
            // Change from List<Long> to List<TimestampedLatency>
            List<TimestampedLatency> latencies = new ArrayList<>();
            try {
                while (!queue.isEmpty() || System.currentTimeMillis() < endTimestamp) {
                    String endpoint = queue.poll(1, TimeUnit.SECONDS);
                    if (endpoint != null) {
                        // Capture request timestamp and latency
                        TimestampedLatency result = sendRequest(endpoint);
                        if (result.getLatency() >= 0) {
                            latencies.add(result);
                            successfulRequests++;
                        }
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                logger.error("Client task interrupted", e);
            } finally {
                try {
                    httpClient.close();
                } catch (IOException e) {
                    logger.error("Error closing HttpClient", e);
                }
            }
            return new ClientTaskResult(latencies, successfulRequests);
        }

        private TimestampedLatency sendRequest(String endpoint) {
            long requestTimestamp = System.currentTimeMillis(); // Record when request was sent
            long start = System.nanoTime();
            HttpGet request = new HttpGet(BASE_URL + endpoint);

            try (CloseableHttpResponse response = httpClient.execute(request)) {
                // Consume the response to free resources
                EntityUtils.consume(response.getEntity());
                // Return latency if successful
                return new TimestampedLatency(requestTimestamp, System.nanoTime() - start);
            } catch (NoHttpResponseException e) {
                logger.error("NoHttpResponseException: The server did not respond. Details:");
                logger.error("Endpoint: {}", endpoint);
                e.printStackTrace();
            } catch (IOException e) {
                logger.error("IOException occurred while sending request to: {}", endpoint);
                logger.error("Message: {}", e.getMessage());
                e.printStackTrace();
            }

            // Indicate failure
            return new TimestampedLatency(requestTimestamp, -1);
        }
    }

    // New class to store a latency with its timestamp
    private static class TimestampedLatency {
        private final long timestamp; // When the request was made
        private final long latency;   // Latency in nanoseconds

        public TimestampedLatency(long timestamp, long latency) {
            this.timestamp = timestamp;
            this.latency = latency;
        }

        public long getTimestamp() {
            return timestamp;
        }

        public long getLatency() {
            return latency;
        }
    }

    private static class ClientTaskResult {
        // Change from List<Long> to List<TimestampedLatency>
        private final List<TimestampedLatency> latencies;
        private final int successfulRequests;

        public ClientTaskResult(List<TimestampedLatency> latencies, int successfulRequests) {
            this.latencies = latencies;
            this.successfulRequests = successfulRequests;
        }

        public List<TimestampedLatency> getLatencies() {
            return latencies;
        }

        public int getSuccessfulRequests() {
            return successfulRequests;
        }
    }

    private static String chooseEndpoint(Map<String, Double> probabilities) {
        double rand = random.nextDouble();
        double cumulative = 0.0;
        for (Map.Entry<String, Double> entry : probabilities.entrySet()) {
            cumulative += entry.getValue();
            if (rand <= cumulative) {
                return ENDPOINTS.get(entry.getKey());
            }
        }
        return ENDPOINTS.values().iterator().next();
    }

    // Replaces writeBenchmarkResults with a method that adds to our global results
    private static void addRunResults(long startTimestamp, long endTimestamp, List<Long> latencyValues,
            List<TimestampedLatency> allLatencies, int totalSuccessfulRequests, int connections, 
            int run, ExperimentConfig experiment, ArrayNode runsArray) throws IOException {
        
        // Create a result node for this run
        ObjectNode runNode = mapper.createObjectNode();
        runNode.put("run_number", run);
        runNode.put("timestamp", System.currentTimeMillis());
        runNode.put("start_timestamp", startTimestamp);
        runNode.put("end_timestamp", endTimestamp);
        runNode.put("elapsed_time_ms", endTimestamp - startTimestamp);
        runNode.put("expected_duration_ms", experiment.getDuration() * 1000);
        runNode.put("terminals", connections);
        runNode.put("connections", experiment.getConnections());
        runNode.put("requests_per_second", experiment.getRequestsPerSecond());
        
        // We don't need to add probabilities to each run since they're now in the experiment config
        // but we'll still track endpoints used
        runNode.put("experiment_name", experiment.getExperimentName());
        
        // Add chronologically ordered latencies with timestamps
        ArrayNode latenciesArray = runNode.putArray("latencies");
        for (TimestampedLatency latency : allLatencies) {
            ObjectNode latencyNode = latenciesArray.addObject();
            latencyNode.put("timestamp", latency.getTimestamp());
            latencyNode.put("latency_ns", latency.getLatency());
        }
        
        // Add latency distribution
        List<Long> sortedLatencies = latencyValues.stream().sorted().collect(Collectors.toList());
        ObjectNode latencyNode = runNode.putObject("latency_distribution");
        if (!sortedLatencies.isEmpty()) {
            latencyNode.put("median_latency_ns", median(sortedLatencies));
            latencyNode.put("min_latency_ns", sortedLatencies.get(0));
            latencyNode.put("max_latency_ns", sortedLatencies.get(sortedLatencies.size() - 1));
            
            // Add percentiles
            ObjectNode percentileNode = latencyNode.putObject("percentiles");
            addPercentile(sortedLatencies, 25, percentileNode);
            addPercentile(sortedLatencies, 75, percentileNode);
            addPercentile(sortedLatencies, 90, percentileNode);
            addPercentile(sortedLatencies, 95, percentileNode);
            addPercentile(sortedLatencies, 99, percentileNode);
        }
        
        // Add performance metrics
        long totalRequests = latencyValues.size();
        double elapsedTimeInSeconds = (endTimestamp - startTimestamp) / 1000.0;
        double throughput = totalRequests / elapsedTimeInSeconds;
        runNode.put("throughput", throughput);
        
        double goodput = totalSuccessfulRequests / elapsedTimeInSeconds;
        runNode.put("goodput", goodput);
        runNode.put("total_requests", totalRequests);
        runNode.put("successful_requests", totalSuccessfulRequests);
        
        // Add this run to the runs array
        runsArray.add(runNode);
        
        // Save intermediate results after each run
        mapper.writeValue(new File(resultFileName), allResults);
        logger.info("Updated results for experiment: {}, run: {}", experiment.getExperimentName(), run);
    }

    private static void addPercentile(List<Long> latencies, int percentile, ObjectNode node) {
        int index = (int) Math.ceil(percentile / 100.0 * latencies.size()) - 1;
        index = Math.max(0, Math.min(index, latencies.size() - 1));
        node.put("p" + percentile, latencies.get(index));
    }

    private static long median(List<Long> latencies) {
        int middle = latencies.size() / 2;
        return latencies.size() % 2 == 0 ? (latencies.get(middle - 1) + latencies.get(middle)) / 2
                : latencies.get(middle);
    }

    private static void createLatencyHistogram(List<Long> latencies, String filePrefix) {
        // Keep the calculation code but comment out the file saving
        try {
            // Convert nanoseconds to milliseconds
            double[] latencyMs = latencies.stream()
                    .mapToDouble(l -> l / 1_000_000.0)
                    .toArray();

            HistogramDataset dataset = new HistogramDataset();
            dataset.addSeries("Latency", latencyMs, 50); // 50 bins

            JFreeChart histogram = ChartFactory.createHistogram(
                    "Latency Distribution",
                    "Latency (ms)",
                    "Frequency",
                    dataset,
                    PlotOrientation.VERTICAL,
                    true,
                    true,
                    false);

            // Generate a file name with experiment info
            String fileName = "latency_histogram_" + filePrefix + ".png";

            // Comment out the image saving code
            /*
            ChartUtils.saveChartAsPNG(
                    new File(fileName),
                    histogram,
                    800,
                    600);
            */
            
            logger.debug("Histogram calculated for {}", filePrefix);
        } catch (Exception e) {
            logger.error("Error creating latency histogram: {}", e.getMessage());
        }
    }

    private static void createLatencyCDF(List<Long> latencies, String filePrefix) {
        // Keep the calculation code but comment out the file saving
        try {
            // Sort latencies and calculate CDF
            List<Long> sortedLatencies = new ArrayList<>(latencies);
            Collections.sort(sortedLatencies);

            XYSeries series = new XYSeries("CDF");
            int totalPoints = sortedLatencies.size();

            for (int i = 0; i < totalPoints; i++) {
                double percentile = (i + 1.0) / totalPoints * 100.0;
                double latencyMs = sortedLatencies.get(i) / 1_000_000.0; // Convert to ms
                series.add(latencyMs, percentile);
            }

            XYSeriesCollection dataset = new XYSeriesCollection(series);

            JFreeChart chart = ChartFactory.createXYLineChart(
                    "Latency Cumulative Distribution Function",
                    "Latency (ms)",
                    "Percentile",
                    dataset,
                    PlotOrientation.VERTICAL,
                    true,
                    true,
                    false);

            // Generate a file name with experiment info
            String fileName = "latency_cdf_" + filePrefix + ".png";

            // Comment out the image saving code
            /*
            ChartUtils.saveChartAsPNG(
                    new File(fileName),
                    chart,
                    800, // width
                    600 // height
            );
            */
            
            logger.debug("CDF calculated for {}", filePrefix);
        } catch (Exception e) {
            logger.error("Error creating latency CDF: {}", e.getMessage());
        }
    }
    
    // XML Configuration Classes
    
    @XmlRootElement(name = "benchmark-config")
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class BenchmarkConfig {
        @XmlElement(name = "pauseBetweenExperiments-ms")
        private int pauseBetweenExperiments;
        
        @XmlElementWrapper(name = "endpoints")
        @XmlElement(name = "endpoint")
        private List<EndpointConfig> endpoints;
        
        @XmlElement(name = "experiment")
        private List<ExperimentConfig> experiments;

        public int getPauseBetweenExperiments() {
            return pauseBetweenExperiments;
        }

        public List<EndpointConfig> getEndpoints() {
            return endpoints;
        }

        public List<ExperimentConfig> getExperiments() {
            return experiments;
        }
    }
    
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class EndpointConfig {
        @XmlAttribute(name = "name")
        private String name;
        
        @XmlValue
        private String url;

        public String getName() {
            return name;
        }

        public String getUrl() {
            return url;
        }
    }
    
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class ExperimentConfig {
        @XmlElement(name = "experiment_name")
        private String experimentName;
        
        @XmlElement(name = "runs")
        private int runs;
        
        @XmlElement(name = "pause-between-runs-ms")
        private int pauseBetweenRuns;
        
        @XmlElement(name = "connections")
        private int connections;
        
        @XmlElement(name = "requests-per-second")
        private int requestsPerSecond;
        
        @XmlElement(name = "duration-seconds")
        private int duration;
        
        @XmlElementWrapper(name = "probabilities")
        @XmlElement(name = "probability")
        private List<ProbabilityConfig> probabilities;
        
        // Helper method to convert probabilities list to a map
        public Map<String, Double> getProbabilitiesMap() {
            Map<String, Double> result = new HashMap<>();
            for (ProbabilityConfig probability : probabilities) {
                result.put(probability.getEndpoint(), probability.getValue());
            }
            return result;
        }

        public String getExperimentName() {
            return experimentName;
        }

        public int getRuns() {
            return runs;
        }

        public int getPauseBetweenRuns() {
            return pauseBetweenRuns;
        }

        public int getConnections() {
            return connections;
        }

        public int getRequestsPerSecond() {
            return requestsPerSecond;
        }

        public int getDuration() {
            return duration;
        }

        public List<ProbabilityConfig> getProbabilities() {
            return probabilities;
        }
    }
    
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class ProbabilityConfig {
        @XmlAttribute(name = "endpoint")
        private String endpoint;
        
        @XmlValue
        private double value;

        public String getEndpoint() {
            return endpoint;
        }

        public double getValue() {
            return value;
        }
    }
}