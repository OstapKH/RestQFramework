package com.restq.utils;

import java.io.*;
import java.nio.file.*;
import java.util.regex.*;
import org.json.JSONArray;
import org.json.JSONObject;

public class JsonFixer {

    public static void fixJsonFilesInFolder(String inputFolder) {
        // Get the input folder path
        Path inputFolderPath = Paths.get(inputFolder);
        if (!Files.isDirectory(inputFolderPath)) {
            System.err.println("The input path is not a directory.");
            return;
        }

        // Process each JSON file in the folder
        try (DirectoryStream<Path> directoryStream = Files.newDirectoryStream(inputFolderPath, "*.json")) {
            for (Path filePath : directoryStream) {
                String content = new String(Files.readAllBytes(filePath));
                JSONArray jsonArray = new JSONArray();

                // Count occurrences of the pattern manually
                int manualCount = 0;
                int lastIndex = 0;
                while ((lastIndex = content.indexOf("{\"host\":", lastIndex)) != -1) {
                    manualCount++;
                    lastIndex += 8; // Move past the current match
                }
                System.out.println("Manual count of JSON objects: " + manualCount);

                // Pattern to match each JSON object, including nested structures
                Pattern pattern = Pattern.compile(
                    "\\{\\s*\"host\"\\s*:\\s*\\{.*?\\}\\s*,\\s*\"consumers\"\\s*:\\s*\\[.*?\\]\\s*,\\s*\"sockets\"\\s*:\\s*\\[.*?\\]\\s*\\}",
                    Pattern.DOTALL
                );
                
                Matcher matcher = pattern.matcher(content);
                int matchCount = 0;
                int validCount = 0;
                
                while (matcher.find()) {
                    matchCount++;
                    String jsonObjectStr = matcher.group();
                    try {
                        // Clean up the JSON string by removing any trailing commas
                        jsonObjectStr = jsonObjectStr.replaceAll(",\\s*}", "}");
                        jsonObjectStr = jsonObjectStr.replaceAll(",\\s*]", "]");
                        
                        JSONObject jsonObject = new JSONObject(jsonObjectStr);
                        if (validateJsonStructure(jsonObject)) {
                            jsonArray.put(jsonObject);
                            validCount++;
                            if (matchCount <= 5) { // Print first 5 entries for verification
                                System.out.println("Entry " + matchCount + " timestamp: " + 
                                    jsonObject.getJSONObject("host").getDouble("timestamp"));
                            }
                        } else {
                            System.out.println("JSON object " + matchCount + " failed validation");
                        }
                    } catch (Exception ex) {
                        System.out.println("Error parsing JSON object " + matchCount + " in file " + filePath.getFileName() + 
                                         ": " + ex.getMessage());
                        // Print the problematic JSON string for debugging
                        System.out.println("Problematic JSON string: " + jsonObjectStr.substring(0, Math.min(200, jsonObjectStr.length())) + "...");
                    }
                }
                
                if (matchCount == 0) {
                    System.out.println("No valid JSON objects found in file " + filePath.getFileName());
                    // Print a sample of the content for debugging
                    System.out.println("Content sample: " + content.substring(0, Math.min(200, content.length())) + "...");
                } else {
                    System.out.println("Found " + matchCount + " JSON objects in file " + filePath.getFileName());
                    System.out.println("Successfully validated: " + validCount + " objects");
                    System.out.println("Manual count: " + manualCount);
                    if (matchCount != manualCount) {
                        System.out.println("WARNING: Manual count differs from regex count!");
                    }
                    if (validCount != matchCount) {
                        System.out.println("WARNING: Some objects failed validation!");
                    }
                }

                // Write the fixed content to the output file in the same folder
                Path outputFilePath = inputFolderPath.resolve("fixed_" + filePath.getFileName());
                try (FileWriter fileWriter = new FileWriter(outputFilePath.toFile())) {
                    fileWriter.write(jsonArray.toString(4)); // Indented output for readability
                    System.out.println("File fixed successfully and saved to " + outputFilePath + 
                                     " with " + jsonArray.length() + " entries");
                    
                    // Verify the output file
                    try {
                        String outputContent = new String(Files.readAllBytes(outputFilePath));
                        JSONArray verifyArray = new JSONArray(outputContent);
                        System.out.println("Verification - Number of entries in output file: " + verifyArray.length());
                        if (verifyArray.length() != validCount) {
                            System.out.println("WARNING: Output file entry count differs from valid count!");
                        }
                    } catch (Exception e) {
                        System.out.println("Warning: Could not verify output file: " + e.getMessage());
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Error processing files in directory: " + e.getMessage());
        }
    }

    private static boolean validateJsonStructure(JSONObject jsonObject) {
        try {
            // Validate top-level fields
            if (!jsonObject.has("host") || !jsonObject.has("consumers") || !jsonObject.has("sockets")) {
                System.out.println("Missing required top-level fields");
                return false;
            }

            // Validate host object
            JSONObject host = jsonObject.getJSONObject("host");
            if (!host.has("consumption") || !host.has("timestamp") || !host.has("components")) {
                System.out.println("Missing required host fields");
                return false;
            }

            // Validate consumers array
            JSONArray consumers = jsonObject.getJSONArray("consumers");
            for (int i = 0; i < consumers.length(); i++) {
                JSONObject consumer = consumers.getJSONObject(i);
                if (!consumer.has("exe") || !consumer.has("cmdline") || !consumer.has("pid") || 
                    !consumer.has("consumption") || !consumer.has("timestamp")) {
                    System.out.println("Missing required consumer fields at index " + i);
                    return false;
                }
            }

            // Validate sockets array
            JSONArray sockets = jsonObject.getJSONArray("sockets");
            for (int i = 0; i < sockets.length(); i++) {
                JSONObject socket = sockets.getJSONObject(i);
                if (!socket.has("id") || !socket.has("consumption") || !socket.has("timestamp")) {
                    System.out.println("Missing required socket fields at index " + i);
                    return false;
                }
            }

            return true;
        } catch (Exception e) {
            System.out.println("Error validating JSON structure: " + e.getMessage());
            return false;
        }
    }
}

