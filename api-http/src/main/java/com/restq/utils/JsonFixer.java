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

                // Identify and separate JSON objects using regex
                Pattern pattern = Pattern.compile("\\{.*?\\}", Pattern.DOTALL);
                Matcher matcher = pattern.matcher(content);

                while (matcher.find()) {
                    String jsonObjectStr = matcher.group();
                    try {
                        JSONObject jsonObject = new JSONObject(jsonObjectStr);
                        jsonArray.put(jsonObject);
                    } catch (Exception e) {
                        System.out.println("Skipping invalid JSON object in file " + filePath.getFileName() + ": " + e.getMessage());
                    }
                }

                // Write the fixed content to the output file in the same folder
                Path outputFilePath = inputFolderPath.resolve("fixed_" + filePath.getFileName());
                try (FileWriter fileWriter = new FileWriter(outputFilePath.toFile())) {
                    fileWriter.write(jsonArray.toString(4)); // Indented output for readability
                    System.out.println("File fixed successfully and saved to " + outputFilePath);
                }
            }
        } catch (IOException e) {
            System.err.println("Error processing files in directory: " + e.getMessage());
        }

    }
}
