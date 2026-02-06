-- =========================
-- FULL NORMALIZED WORKFLOW
-- =========================

BEGIN TRANSACTION;

-- 0) Clean existing associations
DELETE FROM dbo.JobRoleSkill;

-- 1) Define "Unspecified" subcategory ID
DECLARE @UnspecifiedSubCatID UNIQUEIDENTIFIER;

SELECT @UnspecifiedSubCatID = skill_subcategory_id
FROM dbo.skill_subcategories
WHERE LOWER(subcategory_name) = 'unspecified';

IF @UnspecifiedSubCatID IS NULL
    THROW 50000, 'Unspecified subcategory ID not found.', 1;

-- 2) Normalize and upsert missing skills (avoid duplicates by normalized name)
    ;WITH ExtractedSkills AS (
    SELECT DISTINCT
        LOWER(REPLACE(REPLACE(LTRIM(RTRIM(s.value)), '-', ''), ' ', '')) AS norm_name,
        LTRIM(RTRIM(s.value)) AS raw_skill_name
    FROM dbo.JobRole AS jr
             CROSS APPLY STRING_SPLIT(CAST(jr.principalSkills AS VARCHAR(MAX)), '~') AS s
    WHERE jr.principalSkills IS NOT NULL
),
          NormalizedSkills AS (
              SELECT
                  es.norm_name,
                  es.raw_skill_name,
                  ROW_NUMBER() OVER (PARTITION BY es.norm_name ORDER BY es.raw_skill_name) AS rn
              FROM ExtractedSkills AS es
          ),
          CanonicalSkills AS (
              SELECT
                  NEWID() AS skill_id,
                  ns.norm_name,
                  ns.raw_skill_name,
                  @UnspecifiedSubCatID AS skill_subcategory_id,
                  '' AS skill_info_url
              FROM NormalizedSkills AS ns
              WHERE ns.rn = 1
                AND NOT EXISTS (
                  SELECT 1 FROM dbo.skills s
                  WHERE LOWER(REPLACE(REPLACE(s.skill_name, '-', ''), ' ', '')) = ns.norm_name
              )
          )
     INSERT INTO dbo.skills (skill_id, skill_subcategory_id, skill_name, skill_info_url)
     SELECT skill_id, skill_subcategory_id, raw_skill_name, skill_info_url
     FROM CanonicalSkills;

-- 3) Rebuild JobRoleSkill associations
;WITH RoleSkills AS (
    SELECT
        jr.id AS jobRoleId,
        LOWER(REPLACE(REPLACE(LTRIM(RTRIM(s.value)), '-', ''), ' ', '')) AS norm_name
    FROM dbo.JobRole AS jr
             CROSS APPLY STRING_SPLIT(CAST(jr.principalSkills AS VARCHAR(MAX)), '~') AS s
    WHERE jr.principalSkills IS NOT NULL
),
      SkillLookup AS (
          SELECT
              skill_id,
              LOWER(REPLACE(REPLACE(skill_name, '-', ''), ' ', '')) AS norm_name
          FROM dbo.skills
      )
 INSERT INTO dbo.JobRoleSkill (
    id, jobRoleId, skillId, aiImpact, currentProficiency, futureRelevance, trainingRequired
)
 SELECT
     NEWID(),
     rs.jobRoleId,
     sl.skill_id,
     '', '', '', 0
 FROM RoleSkills AS rs
          JOIN SkillLookup AS sl ON rs.norm_name = sl.norm_name
          LEFT JOIN dbo.JobRoleSkill AS jrs
                    ON jrs.jobRoleId = rs.jobRoleId AND jrs.skillId = sl.skill_id
 WHERE jrs.id IS NULL;

COMMIT;

-- =========================
-- SUBCATEGORY MAPPING WORKFLOW
-- =========================

BEGIN TRANSACTION;

-- 1) Declare the in-memory skill → subcategory mapping table
DECLARE @SkillMap TABLE (
                            skill_name VARCHAR(255) NOT NULL,
                            subcategory_name VARCHAR(255)
                        );

-- NOTE: Use INSERT INTO @SkillMap (...) VALUES (...) for each mapping line
-- e.g., ('Problem solving', 'Soft Skill'), etc.
-- You can batch insert up to 1000 per statement if needed.

-- 2) Insert new subcategories from the mapping if missing
INSERT INTO dbo.skill_subcategories (skill_subcategory_id, subcategory_name, subcategory_description)
SELECT NEWID(), m.subcategory_name, ''
FROM (SELECT DISTINCT subcategory_name FROM @SkillMap WHERE subcategory_name IS NOT NULL) AS m
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.skill_subcategories sc
    WHERE LOWER(sc.subcategory_name) = LOWER(m.subcategory_name)
);

-- 3) Update skill entries to use mapped subcategories
UPDATE s
SET s.skill_subcategory_id = sc.skill_subcategory_id
FROM dbo.skills AS s
         INNER JOIN @SkillMap AS m ON LOWER(s.skill_name) = LOWER(m.skill_name)
         INNER JOIN dbo.skill_subcategories AS sc ON LOWER(sc.subcategory_name) = LOWER(m.subcategory_name)
WHERE m.subcategory_name IS NOT NULL
  AND (s.skill_subcategory_id IS NULL OR s.skill_subcategory_id <> sc.skill_subcategory_id);

COMMIT;
