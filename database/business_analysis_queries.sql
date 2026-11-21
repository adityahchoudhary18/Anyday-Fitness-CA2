-- Anyday Fitness: Business Analysis Queries
-- Run these queries after the CA1 dataset has been imported into gym_data.

USE gym_data;

-- 1. Membership distribution and percentage share
SELECT membership_type,
       COUNT(*) AS total_members,
       ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM members), 0), 2) AS percentage_share
FROM members
GROUP BY membership_type
ORDER BY total_members DESC;

-- 2. Average visits and gym duration by membership type
SELECT membership_type,
       ROUND(AVG(visit_per_week), 2) AS average_visits_per_week,
       ROUND(AVG(avg_time_in_gym_min), 2) AS average_gym_duration_minutes
FROM members
GROUP BY membership_type;

-- 3. Personal-training participation by membership type
SELECT membership_type,
       COUNT(*) AS total_members,
       SUM(personal_training = TRUE) AS personal_training_members,
       ROUND(AVG(personal_training) * 100, 2) AS participation_percentage
FROM members
GROUP BY membership_type;

-- 4. Sauna usage by membership type
SELECT membership_type,
       COUNT(*) AS total_members,
       ROUND(AVG(uses_sauna) * 100, 2) AS sauna_usage_percentage
FROM members
GROUP BY membership_type;

-- 5. Group-lesson participation by membership type
SELECT membership_type,
       COUNT(*) AS total_members,
       ROUND(AVG(attend_group_lesson) * 100, 2) AS group_lesson_participation_percentage
FROM members
GROUP BY membership_type;

-- 6. Most frequently selected gym days
SELECT day_name,
       COUNT(*) AS member_selections
FROM member_days
GROUP BY day_name
ORDER BY FIELD(day_name, 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun');

-- 7. Most frequently selected group lessons
SELECT lesson_name,
       COUNT(*) AS selections
FROM member_favorite_lessons
GROUP BY lesson_name
ORDER BY selections DESC, lesson_name;

-- 8. Most frequently selected drinks
SELECT drink_name,
       COUNT(*) AS selections
FROM member_favorite_drinks
GROUP BY drink_name
ORDER BY selections DESC, drink_name;
