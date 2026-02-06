
-- Set skill_type for all soft skills set subcategory for soft skills to Unspecified
BEGIN TRY
    BEGIN TRAN;

    DECLARE
        @SoftSubCatId         UNIQUEIDENTIFIER,
        @UnspecifiedSubCatId  UNIQUEIDENTIFIER;

    -- 1) lookup the two category IDs
    SELECT @SoftSubCatId = skill_subcategory_id
    FROM dbo.skill_subcategories
    WHERE subcategory_name = 'Soft Skill';

    SELECT @UnspecifiedSubCatId = skill_subcategory_id
    FROM dbo.skill_subcategories
    WHERE subcategory_name = 'Unspecified';

    -- 2) do the mass update
    UPDATE dbo.skills
    SET
        skill_type           = 'Soft',
        skill_subcategory_id = @UnspecifiedSubCatId
    WHERE skill_subcategory_id = @SoftSubCatId;

    COMMIT TRAN;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRAN;
    THROW;
END CATCH;

BEGIN TRY
    BEGIN TRAN;

    UPDATE dbo.skills
    SET skill_type = 'Hard'
    WHERE skill_type IS NULL
       OR LTRIM(RTRIM(skill_type)) = '';

    COMMIT TRAN;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRAN;
    THROW;
END CATCH;


-- Add Soft skill categories to the database
BEGIN TRY
    BEGIN TRAN;

    INSERT INTO dbo.skill_subcategories (
        skill_subcategory_id,
        subcategory_name,
        subcategory_description
    )
    SELECT
        NEWID(),
        v.name,
        v.description
    FROM (VALUES
              ('Communication & Influence',             'Effectively conveys complex ideas and persuades diverse stakeholders'),
              ('Relationship Building & Emotional Intelligence', 'Connects authentically with clients, adapts to personalities, and builds trust'),
              ('Adaptability & Learning Agility',       'Thrives in ambiguity, learns quickly, and adjusts to fast product changes'),
              ('Critical Thinking & Problem Solving',   'Navigates customer pain points and maps AI use cases to solutions'),
              ('Entrepreneurial Mindset & Drive',       'Operates with ownership and bias for action in startup environments'),
              ('Team Collaboration & Internal Communication', 'Works with product, engineering, and customer success teams to close the loop'),
              ('Ethical Reasoning & Responsible AI Awareness', 'Navigates ethical issues in AI deployments and builds customer confidence')
         ) AS v(name, description)
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.skill_subcategories sc
        WHERE sc.subcategory_name = v.name
    );

    COMMIT TRAN;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRAN;
    THROW;
END CATCH;


-- Classify each of the soft skills currently in the database under one of the soft skill categories above.
BEGIN TRY
    BEGIN TRAN;

    UPDATE s
    SET s.skill_subcategory_id = CASE

        -- 1) Team Collaboration & Internal Communication
                                     WHEN s.skill_name IN (
                                                           'Teamwork and collaboration',
                                                           'Coordinating',
                                                           'Workflow management',
                                                           'Documentation maintenance',
                                                           'Task coordination',
                                                           'Project team management',
                                                           'Cross functional team leadership'
                                         )
                                         THEN (SELECT skill_subcategory_id
                                               FROM dbo.skill_subcategories
                                               WHERE subcategory_name = 'Team Collaboration & Internal Communication')

        -- 2) Communication & Influence
                                     WHEN s.skill_name IN (
                                                           'Presentations',
                                                           'Presentation',
                                                           'Presentation skills',
                                                           'Active listening',
                                                           'Excellent verbal and written communication',
                                                           'Verbal and written communications',
                                                           'Writing',
                                                           'Communication',
                                                           'Effective communication',
                                                           'Communicate findings to stakeholders',
                                                           'Describe scenarios',
                                                           'Digital marketing',
                                                           'Conversationalist',
                                                           'Strong communication'
                                         )
                                         THEN (SELECT skill_subcategory_id
                                               FROM dbo.skill_subcategories
                                               WHERE subcategory_name = 'Communication & Influence')

        -- 3) Critical Thinking & Problem Solving
                                     WHEN s.skill_name IN (
                                                           'Critical thinking',
                                                           'Problem-solving',
                                                           'Problem solving',
                                                           'Customer problem solving',
                                                           'Analytical thinking',
                                                           'Investigation',
                                                           'Complex problem-solving',
                                                           'Critical problem solving',
                                                           'Decision making',
                                                           'Research information',
                                                           'Analytical skills',
                                                           'Analytical skills to identify root causes of issues'
                                         )
                                         THEN (SELECT skill_subcategory_id
                                               FROM dbo.skill_subcategories
                                               WHERE subcategory_name = 'Critical Thinking & Problem Solving')

        -- 4) Adaptability & Learning Agility
                                     WHEN s.skill_name IN (
                                                           'Make iterations',
                                                           'Knowledge base maintenance',
                                                           'Adaptability',
                                                           'Multitasking',
                                                           'Time management',
                                                           'Prioritization',
                                                           'Prioritization and multitasking',
                                                           'Ability to think creatively and adapt to different situations',
                                                           'Process improvement',
                                                           'Continuous process improvement'
                                         )
                                         THEN (SELECT skill_subcategory_id
                                               FROM dbo.skill_subcategories
                                               WHERE subcategory_name = 'Adaptability & Learning Agility')

        -- 5) Entrepreneurial Mindset & Drive
                                     WHEN s.skill_name IN (
                                                           'Demonstrating responsibility',
                                                           'Innovation',
                                                           'Leadership demonstration',
                                                           'Leadership',
                                                           'New product development',
                                                           'Self-motivation',
                                                           'Strategic planning',
                                                           'Finance'
                                         )
                                         THEN (SELECT skill_subcategory_id
                                               FROM dbo.skill_subcategories
                                               WHERE subcategory_name = 'Entrepreneurial Mindset & Drive')

        -- 6) Relationship Building & Emotional Intelligence
                                     WHEN s.skill_name IN (
                                                           'Customer service',
                                                           'Patience and ability to handle difficult situations',
                                                           'Strong customer focus and empathy',
                                                           'Empathy',
                                                           'Emotional intelligence',
                                                           'Customer relationship management',
                                                           'Vendor management'
                                         )
                                         THEN (SELECT skill_subcategory_id
                                               FROM dbo.skill_subcategories
                                               WHERE subcategory_name = 'Relationship Building & Emotional Intelligence')

        -- 7) Ethical Reasoning & Responsible AI Awareness
        -- (currently no direct matches in the soft skills list)

        -- Else: leave as-is (i.e. stay Unspecified)
                                     ELSE s.skill_subcategory_id
        END
    FROM dbo.skills AS s
    WHERE s.skill_type = 'Soft';

    COMMIT TRAN;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRAN;
    THROW;
END CATCH;
