package com.restq.api_http.Benchmark;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.Collectors;

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

public class ApiBenchmark {

    private static final Logger logger = LoggerFactory.getLogger(ApiBenchmark.class);

    private static final String CONFIG_FILE = "src/main/resources/config.json";
    private static final String BASE_URL = "http://localhost:8086/api/reports";
    private static Map<String, String> ENDPOINTS;

    private static final Random random = new Random();

    // Map to track the initial port used by each thread
    private static final ConcurrentMap<String, Integer> initialPortMap = new ConcurrentHashMap<>();

    public static void main(String[] args) throws IOException, InterruptedException {
        Config config = new ObjectMapper().readValue(new File(CONFIG_FILE), Config.class);
        ENDPOINTS = config.getEndpoints();

        for (int run = 0; run < 3; run++) {
            // Clear initial port map for each run
            initialPortMap.clear();

            ExecutorService executor = Executors.newFixedThreadPool(config.getConnections());
            List<Future<ClientTaskResult>> futures = new ArrayList<>();
            List<Long> allLatencies = new ArrayList<>();

            // Create a queue for each thread
            List<BlockingQueue<String>> queues = new ArrayList<>();
            for (int i = 0; i < config.getConnections(); i++) {
                queues.add(new LinkedBlockingQueue<>());
            }

            long startTimestamp = System.currentTimeMillis();
            long endTimestamp = startTimestamp + config.getDuration() * 1000;

            // Start producer thread to add requests to queues
            Thread producerThread = new Thread(() -> {
                try {
                    while (System.currentTimeMillis() < endTimestamp) {
                        long startTime = System.currentTimeMillis();
                        String endpoint = chooseEndpoint(config.getProbabilities());

                        for (BlockingQueue<String> queue : queues) {
                            for (int j = 0; j < config.getRequestsPerSecond(); j++) {
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
            for (int i = 0; i < config.getConnections(); i++) {
                futures.add(executor.submit(new ClientTask(config, queues.get(i), endTimestamp)));
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

            executor.shutdown();
            executor.awaitTermination(2, TimeUnit.SECONDS);

            long actualEndTimestamp = System.currentTimeMillis();

            writeBenchmarkResults(startTimestamp, actualEndTimestamp, allLatencies, totalSuccessfulRequests,
                    config.getConnections(), run);

            Thread.sleep(10000);
        }
    }

    private static class ClientTask implements Callable<ClientTaskResult> {
        private final Config config;
        private final CloseableHttpClient httpClient;
        private final BlockingQueue<String> queue;
        private final long endTimestamp;
        private int successfulRequests = 0; // Track successful requests
        private final String threadName;

        public ClientTask(Config config, BlockingQueue<String> queue, long endTimestamp) {
            this.config = config;
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
            List<Long> latencies = new ArrayList<>();
            try {
                while (!queue.isEmpty() || System.currentTimeMillis() < endTimestamp) {
                    String endpoint = queue.poll(1, TimeUnit.SECONDS);
                    if (endpoint != null) {
                        long latency = sendRequest(endpoint);
                        if (latency >= 0) {
                            latencies.add(latency);
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

        private long sendRequest(String endpoint) {
            long start = System.nanoTime();
            HttpGet request = new HttpGet(BASE_URL + endpoint);

            try (CloseableHttpResponse response = httpClient.execute(request)) {
                // Consume the response to free resources
                EntityUtils.consume(response.getEntity());
                // Return latency if successful
                return System.nanoTime() - start;
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
            return -1;
        }
    }

    private static class ClientTaskResult {
        private final List<Long> latencies;
        private final int successfulRequests;

        public ClientTaskResult(List<Long> latencies, int successfulRequests) {
            this.latencies = latencies;
            this.successfulRequests = successfulRequests;
        }

        public List<Long> getLatencies() {
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

    private static void writeBenchmarkResults(long startTimestamp, long endTimestamp, List<Long> latencies,
            int totalSuccessfulRequests, int connections, int run) throws IOException {
        Config config = new ObjectMapper().readValue(new File(CONFIG_FILE), Config.class);

        BenchmarkResult result = new BenchmarkResult();
        result.setTimestamp(System.currentTimeMillis());
        result.setStartTimestamp(startTimestamp);
        result.setCurrentTimestamp(endTimestamp);
        result.setElapsedTime(endTimestamp - startTimestamp);
        result.setExpectedDuration(config.getDuration() * 1000);
        result.setTerminals(connections);
        result.setConnections(config.getConnections());
        result.setRequestsPerSecond(config.getRequestsPerSecond());
        result.setProbabilities(config.getProbabilities());
        result.setEndpoints(config.getEndpoints());

        List<Long> sortedLatencies = latencies.stream().sorted().collect(Collectors.toList());
        result.setLatencyDistribution(createLatencyDistribution(sortedLatencies));

        long totalRequests = latencies.size();
        double elapsedTimeInSeconds = (endTimestamp - startTimestamp) / 1000.0;
        double throughput = totalRequests / elapsedTimeInSeconds;
        result.setThroughput(throughput);

        double goodput = totalSuccessfulRequests / elapsedTimeInSeconds;
        result.setGoodput(goodput);

        // Generate a timestamped file name
        String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
        String fileName = "benchmark_results_" + timestamp + ".json";

        // Write the result to a new file
        ObjectMapper mapper = new ObjectMapper();
        mapper.writeValue(new File(fileName), result);

        // Create visualizations
        createLatencyHistogram(latencies, timestamp);
        createLatencyCDF(latencies, timestamp);
    }

    private static LatencyDistribution createLatencyDistribution(List<Long> latencies) {
        LatencyDistribution distribution = new LatencyDistribution();
        distribution.setMedianLatency(median(latencies));
        distribution.setMinimumLatency(latencies.get(0));
        distribution.setMaximumLatency(latencies.get(latencies.size() - 1));
        distribution.setPercentile(latencies, 25, 75, 90, 95, 99);
        return distribution;
    }

    private static long median(List<Long> latencies) {
        int middle = latencies.size() / 2;
        return latencies.size() % 2 == 0 ? (latencies.get(middle - 1) + latencies.get(middle)) / 2
                : latencies.get(middle);
    }

    private static void createLatencyHistogram(List<Long> latencies, String timestamp) {
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

            // Generate a timestamped file name
            String fileName = "latency_histogram_" + timestamp + ".png";

            // Save the chart as PNG
            ChartUtils.saveChartAsPNG(
                    new File(fileName),
                    histogram,
                    800,
                    600);
        } catch (IOException e) {
            logger.error("Error creating latency histogram: {}", e.getMessage());
        }
    }

    private static void createLatencyCDF(List<Long> latencies, String timestamp) {
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

            // Generate a timestamped file name
            String fileName = "latency_cdf_" + timestamp + ".png";

            // Save the chart as PNG
            ChartUtils.saveChartAsPNG(
                    new File(fileName),
                    chart,
                    800, // width
                    600 // height
            );
        } catch (IOException e) {
            logger.error("Error creating latency CDF: {}", e.getMessage());
        }
    }
}