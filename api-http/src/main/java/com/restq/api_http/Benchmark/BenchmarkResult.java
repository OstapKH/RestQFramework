package com.restq.api_http.Benchmark;

public class BenchmarkResult {
    private long startTimestamp;
    private long currentTimestamp;
    private long elapsedTime;
    private int terminals;
    private LatencyDistribution latencyDistribution;
    private double throughput;
    private double goodput;
    private long expectedDuration;

    public long getStartTimestamp() {
        return startTimestamp;
    }

    public void setStartTimestamp(long startTimestamp) {
        this.startTimestamp = startTimestamp;
    }

    public long getCurrentTimestamp() {
        return currentTimestamp;
    }

    public void setCurrentTimestamp(long currentTimestamp) {
        this.currentTimestamp = currentTimestamp;
    }

    public long getElapsedTime() {
        return elapsedTime;
    }

    public void setElapsedTime(long elapsedTime) {
        this.elapsedTime = elapsedTime;
    }

    public LatencyDistribution getLatencyDistribution() {
        return latencyDistribution;
    }

    public void setLatencyDistribution(LatencyDistribution latencyDistribution) {
        this.latencyDistribution = latencyDistribution;
    }

    public double getThroughput() {
        return throughput;
    }

    public void setThroughput(double throughput) {
        this.throughput = throughput;
    }

    public double getGoodput() {
        return goodput;
    }

    public void setGoodput(double goodput) {
        this.goodput = goodput;
    }

    public int getTerminals() {
        return terminals;
    }

    public void setTerminals(int terminals) {
        this.terminals = terminals;
    }

    public long getExpectedDuration() {
        return expectedDuration;
    }

    public void setExpectedDuration(long expectedDuration) {
        this.expectedDuration = expectedDuration;
    }
}


