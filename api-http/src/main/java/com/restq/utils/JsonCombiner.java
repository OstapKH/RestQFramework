package com.restq.utils;

import java.io.*;
import java.nio.file.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.text.SimpleDateFormat;
import java.util.Date;

public class JsonCombiner {
    public static void main(String[] args) {
       if (args.length < 2) {
           System.err.println("Usage: JsonCombiner <inputDirectory> <outputFile>");
           System.exit(1);
       }

       String inputDir = args[0];
       String outputFile = args[1];

        try {
            // First fix all JSON files in the directory
            JsonFixer.fixJsonFilesInFolder(inputDir);
            
            // Now combine the fixed files
            JSONObject combinedJson = new JSONObject();
            String timestamp = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date());
            combinedJson.put("timestamp", timestamp);
            
            // Directory with fixed files
            Path fixedDir = Paths.get(inputDir);
            
            // Get all fixed JSON files
            List<Path> fixedFiles = new ArrayList<>();
            try (DirectoryStream<Path> stream = Files.newDirectoryStream(fixedDir, "fixed_*.json")) {
                for (Path path : stream) {
                    fixedFiles.add(path);
                }
            }
            
            // Find benchmark results file
            Path benchmarkFile = null;
            try (DirectoryStream<Path> stream = Files.newDirectoryStream(fixedDir, "benchmark_results_*.json")) {
                for (Path path : stream) {
                    benchmarkFile = path;
                    break;
                }
            }
            
            // Add benchmark results if found
            if (benchmarkFile != null) {
                String benchmarkContent = new String(Files.readAllBytes(benchmarkFile));
                JSONObject benchmarkJson = new JSONObject(benchmarkContent);
                combinedJson.put("benchmark_results", benchmarkJson);
            }
            
            // Add energy measurements
            for (Path fixedFile : fixedFiles) {
                String filename = fixedFile.getFileName().toString();
                String content = new String(Files.readAllBytes(fixedFile));
                
                JSONArray jsonArray = new JSONArray(content);
                
                if (filename.contains("dbserver")) {
                    combinedJson.put("db_server_energy", jsonArray);
                } else if (filename.contains("apiserver")) {
                    combinedJson.put("api_server_energy", jsonArray);
                }
            }
            
            // Write the combined file
            try (FileWriter writer = new FileWriter(outputFile)) {
                writer.write(combinedJson.toString(4));
                System.out.println("Combined JSON written to " + outputFile);
            }
            
        } catch (Exception e) {
            System.err.println("Error combining JSON files: " + e.getMessage());
            e.printStackTrace();
        }
    }
} 

