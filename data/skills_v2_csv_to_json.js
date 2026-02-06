const fs = require("fs");
const path = require("path");
const csv = require("csv-parser");

const inputFilePath = path.join(__dirname, "skills_v2.csv");
const outputFilePath = path.join(__dirname, "skills_v2.mjs");

const results = [];

fs.createReadStream(inputFilePath)
  .pipe(csv())
  .on("data", (data) => {
    // Replace null or empty info_url with an empty string
    if (data.info_url === "NULL") {
      data.info_url = "";
    }
    results.push({
      skill_category: data.skill_category,
      skill: data.skill,
      info_url: data.info_url,
    });
  })
  .on("end", () => {
    const jsonContent = `const skillsData_v2 = ${JSON.stringify(results, null, 2)};\nexport default skillsData_v2`;
    fs.writeFileSync(outputFilePath, jsonContent);
    console.log(`Converted JSON saved to ${outputFilePath}`);
  });
