const fs = require("fs");
const path = require("path");
const csv = require("csv-parser");

function convertCsvToJson(filePath, outputJsonPath) {
  const postalCodes = [];

  console.log("Converting CSV to JSON...");
  return new Promise((resolve, reject) => {
    fs.createReadStream(path.resolve(__dirname, filePath))
      .pipe(csv())
      .on("data", (row) => {
        const postalCode = {
          zip: row.zip.toString().padStart(5, "0"),
          city: row.city,
          county: row.county_name,
          stateCode: row.state_id,
          state: row.state_name,
          lat: parseFloat(row.lat),
          lng: parseFloat(row.lng),
        };
        postalCodes.push(postalCode);
      })
      .on("end", () => {
        // Write the JSON data to a file
        fs.writeFileSync(outputJsonPath, JSON.stringify(postalCodes, null, 2));
        console.log(`CSV converted to JSON and saved to ${outputJsonPath}`);
        resolve();
      })
      .on("error", (error) => {
        console.error("Error reading CSV file:", error);
        reject(error);
      });
  });
}

// Usage example
const csvFilePath = "../data/talent_finder_zips.csv"; // Replace with your CSV file path
const outputJsonPath = "../data/postal_geo_data.json"; // Replace with your desired JSON file path
convertCsvToJson(csvFilePath, outputJsonPath)
  .then(() => console.log("Conversion completed successfully."))
  .catch((error) => console.error("Error during conversion:", error));
