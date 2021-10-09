DROP TABLE IF EXISTS students CASCADE; 
DROP TABLE IF EXISTS works CASCADE;
DROP TABLE IF EXISTS total_grades;
DROP SEQUENCE IF EXISTS seq_student_id CASCADE;

CREATE TABLE students (
	student_id int PRIMARY KEY,
	student_name varchar(50) NOT NULL,
	student_login varchar(10) NOT NULL,
	student_password varchar(200) NOT NULL,
	student_row integer,
	mana_earned integer DEFAULT 0,
	last_homework_id integer DEFAULT 5,
	last_classwork_id integer DEFAULT 1,
	homework_lvl integer DEFAULT 1,
	classwork_lvl integer DEFAULT 1
);

CREATE SEQUENCE seq_student_id
START WITH 1
OWNED BY students.student_id;

ALTER TABLE students
ALTER COLUMN student_id SET DEFAULT nextval('seq_student_id');

CREATE TABLE works (
	work_id serial PRIMARY KEY,
	work_name varchar(100) NOT NULL,
	sheet_name varchar(100) NOT NULL,
	grades_string varchar NOT NULL,
	is_homework boolean NOT NULL
);

CREATE TABLE total_grades (
	fk_student_id integer REFERENCES students(student_id) NOT NULL,
	fk_work_id integer REFERENCES works(work_id) NOT NULL,
	score integer,
	max_score integer,
	exercises integer,
	mana integer
);

DROP FUNCTION IF EXISTS get_current_classwork_score;
CREATE OR REPLACE FUNCTION get_current_classwork_score(IN current_student_id integer, IN current_work_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	JOIN works ON works.work_id = total_grades.fk_work_id
	WHERE total_grades.fk_student_id = current_student_id AND works.work_id = current_work_id AND works.is_homework = 'False';
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_current_homework_score;
CREATE OR REPLACE FUNCTION get_current_homework_score(IN current_student_id integer, IN current_work_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	JOIN works ON works.work_id = total_grades.fk_work_id
	WHERE total_grades.fk_student_id = current_student_id AND works.work_id = current_work_id AND works.is_homework = 'True';
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_last_homework_score;
CREATE OR REPLACE FUNCTION get_last_homework_score(IN current_student_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	RIGHT JOIN students ON fk_student_id = student_id
	WHERE student_id = current_student_id AND fk_work_id = last_homework_id;
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_last_classwork_score;
CREATE OR REPLACE FUNCTION get_last_classwork_score(IN current_student_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	RIGHT JOIN students ON fk_student_id = student_id
	WHERE student_id = current_student_id AND fk_work_id = last_classwork_id;
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_current_homework_progress;
CREATE OR REPLACE FUNCTION get_current_homework_progress(IN current_student_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	RIGHT JOIN students ON fk_student_id = student_id
	RIGHT JOIN works ON fk_work_id = work_id
	WHERE student_id = current_student_id AND fk_work_id <= last_homework_id AND is_homework = 'True';
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_current_classwork_progress;
CREATE OR REPLACE FUNCTION get_current_classwork_progress(IN current_student_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	RIGHT JOIN students ON fk_student_id = student_id
	RIGHT JOIN works ON fk_work_id = work_id
	WHERE student_id = current_student_id AND fk_work_id <= last_classwork_id AND is_homework = 'False';
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS waiting_for_mana;
CREATE OR REPLACE FUNCTION waiting_for_mana() RETURNS TABLE(student_id integer, student_name varchar(50), mana_earned integer, mana bigint) AS $$
	SELECT student_id, student_name, mana_earned, SUM(mana) AS mana_new FROM students
	JOIN total_grades ON student_id = fk_student_id
	JOIN works ON fk_work_id = work_id
	WHERE is_homework = 'True'
	GROUP BY student_name, mana_earned, student_id
	HAVING mana_earned - SUM(mana) < 0
	ORDER BY student_id;
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_homeworks_progress_others;
CREATE OR REPLACE FUNCTION get_homeworks_progress_others(IN current_student_id integer, OUT others_perc double precision) AS $$
	SELECT ROUND(AVG(perc)*100::numeric)
	FROM (SELECT fk_student_id, CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT) AS perc
	FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE total_grades.fk_student_id != current_student_id AND works.is_homework = 'True' AND fk_work_id < last_homework_id
	GROUP BY fk_student_id
	ORDER BY fk_student_id) AS select_for_function
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_classworks_progress_others;
CREATE OR REPLACE FUNCTION get_classworks_progress_others(IN current_student_id integer, OUT others_perc double precision) AS $$
	SELECT ROUND(AVG(perc)*100::numeric)
	FROM (SELECT fk_student_id, CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT) AS perc
	FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE total_grades.fk_student_id != current_student_id AND works.is_homework = 'False' AND fk_work_id < last_classwork_id
	GROUP BY fk_student_id
	ORDER BY fk_student_id) AS select_for_function
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_themes;
CREATE OR REPLACE FUNCTION get_themes(IN current_student_id integer) RETURNS SETOF varchar AS $$
	SELECT DISTINCT sheet_name
	FROM works
	JOIN total_grades ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE is_homework = 'True'
	AND sheet_name NOT LIKE 'Экзамен%' AND student_id = current_student_id AND work_id <= last_homework_id;
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_last_homework_others;
CREATE OR REPLACE FUNCTION get_last_homework_others(IN current_student_id integer, IN current_work_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	RIGHT JOIN students ON fk_student_id != student_id
	WHERE student_id = current_student_id AND fk_work_id = last_homework_id;
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_last_classwork_others;
CREATE OR REPLACE FUNCTION get_last_classwork_others(IN current_student_id integer, IN current_work_id integer, OUT perc double precision) AS $$
	SELECT ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	RIGHT JOIN students ON fk_student_id != student_id
	WHERE student_id = current_student_id AND fk_work_id = last_classwork_id;
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS comparing_last_classwork;
CREATE OR REPLACE FUNCTION comparing_last_classwork(IN current_student_id integer, OUT perc double precision) AS $$
	SELECT * FROM get_last_classwork_others(current_student_id, (SELECT last_classwork_id FROM students WHERE student_id = current_student_id))
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS comparing_last_homework;
CREATE OR REPLACE FUNCTION comparing_last_homework(IN current_student_id integer, OUT perc double precision) AS $$
	SELECT * FROM get_last_homework_others(current_student_id, (SELECT last_homework_id FROM students WHERE student_id = 1))
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_exam_score;
CREATE OR REPLACE FUNCTION get_exam_score(IN current_student_id integer) RETURNS TABLE(work_id integer, grade integer) AS $$
	SELECT fk_work_id, score FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE sheet_name = 'Экзамен письм дз(баллы 2007)' AND fk_student_id = current_student_id AND last_homework_id >= fk_work_id
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_exam_score_others;
CREATE OR REPLACE FUNCTION get_exam_score_others(IN current_student_id integer) RETURNS TABLE(others_work_id integer, others_grade double precision) AS $$
	SELECT fk_work_id, CAST(AVG(score) as FLOAT) FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE sheet_name = 'Экзамен письм дз(баллы 2007)' AND fk_student_id != current_student_id AND (SELECT last_homework_id FROM students WHERE student_id = current_student_id) >= fk_work_id AND last_homework_id >= fk_work_id
	GROUP BY fk_work_id
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS compare_exams;
CREATE OR REPLACE FUNCTION compare_exams(IN current_student_id integer) RETURNS TABLE(current_student_grades integer, others_grade double precision) AS $$
	SELECT grade, others_grade FROM get_exam_score(current_student_id)
	JOIN (SELECT * FROM get_exam_score_others(current_student_id)) AS other_students ON work_id = others_work_id
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_exam_score_speaking;
CREATE OR REPLACE FUNCTION get_exam_score_speaking(IN current_student_id integer) RETURNS TABLE(work_id integer, grade integer) AS $$
	SELECT fk_work_id, score FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE sheet_name = 'Экзамен устный дз' AND fk_student_id = current_student_id AND last_homework_id >= fk_work_id
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_exam_score_others_speaking;
CREATE OR REPLACE FUNCTION get_exam_score_others_speaking(IN current_student_id integer) RETURNS TABLE(others_work_id integer, others_grade double precision) AS $$
	SELECT fk_work_id, CAST(AVG(score) as FLOAT) FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE sheet_name = 'Экзамен устный дз' AND fk_student_id != current_student_id AND (SELECT last_homework_id FROM students WHERE student_id = current_student_id) >= fk_work_id AND last_homework_id >= fk_work_id
	GROUP BY fk_work_id
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS compare_exams_speaking;
CREATE OR REPLACE FUNCTION compare_exams_speaking(IN current_student_id integer) RETURNS TABLE(current_student_grades integer, others_grade double precision) AS $$
	SELECT grade, others_grade FROM get_exam_score_speaking(current_student_id)
	JOIN (SELECT * FROM get_exam_score_others_speaking(current_student_id)) AS other_students ON work_id = others_work_id
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_themes_score;
CREATE OR REPLACE FUNCTION get_themes_score(IN current_student_id integer) RETURNS TABLE(work_id integer, theme varchar, grade integer) AS $$
	SELECT fk_work_id, LEFT(sheet_name, -3), CAST(ROUND((CAST(score as FLOAT) / CAST(max_score as FLOAT))*100::numeric) AS INTEGER) FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE sheet_name NOT LIKE 'Экзамен%' AND fk_student_id = current_student_id AND last_homework_id >= fk_work_id AND is_homework = 'True'
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_themes_score_others;
CREATE OR REPLACE FUNCTION get_themes_score_others(IN current_student_id integer) RETURNS TABLE(others_work_id integer, theme varchar, others_grade integer) AS $$
	SELECT fk_work_id,  LEFT(sheet_name, -3), CAST(AVG(ROUND((CAST(score as FLOAT) / CAST(max_score as FLOAT))*100::numeric)) AS INTEGER) FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE sheet_name NOT LIKE 'Экзамен%' AND fk_student_id != current_student_id AND (SELECT last_homework_id FROM students WHERE student_id = current_student_id) >= fk_work_id AND is_homework = 'True' AND last_homework_id >= fk_work_id
	GROUP BY fk_work_id, sheet_name
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS compare_themes;
CREATE OR REPLACE FUNCTION compare_themes(IN current_student_id integer) RETURNS TABLE(theme varchar, current_student_grades integer, others_grade integer) AS $$
	SELECT get_themes_score.theme, grade, others_grade FROM get_themes_score(current_student_id)
	JOIN (SELECT * FROM get_themes_score_others(current_student_id)) AS other_students ON work_id = others_work_id
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_sum_homeworks_score;
CREATE OR REPLACE FUNCTION get_sum_homeworks_score(IN current_student_id integer, OUT current_max_score bigint, OUT current_score bigint) AS $$
	SELECT SUM(max_score), SUM(score) FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE fk_student_id = current_student_id and is_homework = 'True'
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_sum_classworks_score;
CREATE OR REPLACE FUNCTION get_sum_classworks_score(IN current_student_id integer, OUT current_max_score bigint, OUT current_score bigint) AS $$
	SELECT SUM(max_score), SUM(score) FROM total_grades
	JOIN works ON fk_work_id = work_id
	JOIN students ON fk_student_id = student_id
	WHERE fk_student_id = current_student_id and is_homework = 'False'
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS get_all_homeworks_perc;
CREATE OR REPLACE FUNCTION get_all_homeworks_perc(IN current_student_id integer) RETURNS TABLE(work_id integer, perc double precision) AS $$
	SELECT work_id, ROUND((CAST(SUM(score) as FLOAT) / CAST(SUM(max_score) as FLOAT))*100::numeric)
	FROM total_grades
	JOIN works ON works.work_id = total_grades.fk_work_id
	JOIN students ON fk_student_id = student_id
	WHERE total_grades.fk_student_id = current_student_id AND works.is_homework = 'True' AND work_id <= last_homework_id
	GROUP BY work_id
	ORDER BY work_id;
$$ LANGUAGE SQL;

DROP FUNCTION IF EXISTS set_mana;
CREATE OR REPLACE FUNCTION set_mana(IN current_student_id integer) RETURNS void AS $$
DECLARE
    work_id integer;
	perc double precision;
	mana_x integer = 0;
BEGIN
FOR work_id, perc IN
    SELECT * FROM get_all_homeworks_perc(current_student_id)
LOOP
	IF perc <= 25 THEN
		mana_x := 1;
	ELSIF 25 < perc AND perc <= 50 THEN
		mana_x := 2;
	ELSIF 50 < perc AND perc <= 75 THEN
		mana_x := 3;
	ELSIF 75 < perc AND perc <= 100 THEN
		mana_x := 4;
	END IF;
	UPDATE total_grades SET mana = mana_x WHERE fk_student_id = current_student_id AND fk_work_id = work_id;
END LOOP;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS set_mana_everyone;
CREATE OR REPLACE FUNCTION set_mana_everyone() RETURNS void AS $$
DECLARE
    current_student_id integer;
BEGIN
FOR current_student_id IN
    SELECT student_id FROM students WHERE student_id < 999
LOOP
	PERFORM set_mana(current_student_id);
END LOOP;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS set_lvl;
CREATE OR REPLACE FUNCTION set_lvl(IN current_student_id integer) RETURNS void AS $$
DECLARE
	score integer;
	lvl integer = 0;
BEGIN
FOR score IN
    SELECT current_score FROM get_sum_homeworks_score(current_student_id)
LOOP
	IF score < 50 THEN
		lvl := 1;
	ELSIF 50 <= score AND score < 110 THEN
		lvl := 2;
	ELSIF 110 <= score AND score < 180 THEN
		lvl := 3;
	ELSIF 180 <= score AND score < 260 THEN
		lvl := 4;
	ELSIF 260 <= score AND score < 350 THEN
		lvl := 5;
	ELSIF 350 <= score AND score < 450 THEN
		lvl := 6;
	ELSIF 450 <= score AND score < 560 THEN
		lvl := 7;
	ELSIF 560 <= score AND score < 680 THEN
		lvl := 8;
	ELSIF 680 <= score AND score < 810 THEN
		lvl := 9;
	ELSIF 810 <= score AND score < 950 THEN
		lvl := 10;
	ELSIF 950 <= score AND score < 1100 THEN
		lvl := 11;
	ELSIF 1100 <= score THEN
		lvl := 12;
	END IF;
	UPDATE students SET homework_lvl = lvl WHERE student_id = current_student_id;
END LOOP;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS set_lvl_everyone;
CREATE OR REPLACE FUNCTION set_lvl_everyone() RETURNS void AS $$
DECLARE
    current_student_id integer;
BEGIN
FOR current_student_id IN
    SELECT student_id FROM students WHERE student_id < 999
LOOP
	PERFORM set_lvl(current_student_id);
END LOOP;
END;
$$ LANGUAGE plpgsql;