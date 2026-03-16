# What I Tested

I evaluated JSearch's data coverage and accuracy by comparing its output against the source job postings on their respective websites, with a focus on listings targeting the El Paso region.  
# What I Found  
JSearch accurately retrieves and reflects the information available in each job posting. No false or fabricated data was observed. However, its completeness is bounded by what the job boards publicly disclose. The most consistently missing field was salary, which was null across the majority of results. This is a limitation of the source postings themselves rather than a flaw in JSearch's behavior.  
# Recommendation  
Use the ‘site’ parameter in JSearch API calls to target job boards known to fully disclose job details without requiring a login. Prioritizing these sources will improve the completeness of the data returned. When providing the ‘site’ parameter to target job boards with more information available JSearch is a powerful tool. My recommendation is to keep JSearch as the authoritative source of truth when paired with other tools with the caveat of targeting Job boards that have public available information to get comprehensive results.   
# Tradeoffs Acknowledged  
JSearch is constrained by the information available in the original job postings. Boards that gate details behind a login will always return incomplete records. That said, JSearch delivers a clean, consistent response format and reliably surfaces whatever is publicly available and that makes it a solid foundation as long as source selection is managed carefully.  
# Data / Evidence  
The output is faithful to each job description as publicly listed. The primary limitation is source-side: if a posting requires login to view full details, JSearch cannot access or return that information. Targeting open-access job boards directly addresses this gap

### Example 1:
Context: In the job posting there was no access to any salary information without login. 

Output:

"state": "Texas",
"country": "US",
"is_remote": false,
"date_posted": "2026-02-19T00:00:00",
"date_ingested": "2026-03-12T18:33:32.920109",
"salary_raw": null,
"salary_min": null,
"salary_max": null,
"salary_currency": null,
"salary_period": null,


### Example 2:

Context: Similar to the previous example salary information did not provide salary information without login.

"city": "El Paso",
"state": "Texas",
"country": "US",
"is_remote": false,
"date_posted": "2026-03-05T00:00:00",
"date_ingested": "2026-03-12T18:33:32.920170",
"salary_raw": null,
"salary_min": null,
"salary_max": null,
"salary_currency": null,
"salary_period": null,
"employment_type": "Full-time",



### Example 3:

Context: When using the site parameter in the JSearch API call with target websites that I knew had public salary information (meaning no login requried), the results were more complete. The results had more information such salary min and max.  

"city": "El Paso",
"state": "Texas",
"country": "US",
"is_remote": true,
"date_posted": null,
"date_ingested": "2026-03-12T19:06:30.163082",
"salary_raw": null,
"salary_min": 80.0,
"salary_max": 120.0,
"salary_currency": null,
"salary_period": "HOUR",
"employment_type": "Full-time",
"experience_level": null,