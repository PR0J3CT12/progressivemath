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
	mana_earned integer,
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