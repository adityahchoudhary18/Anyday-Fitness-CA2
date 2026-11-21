-- Anyday Fitness Management System
-- Execute this script in MySQL Workbench before importing the CA1 dataset.

CREATE DATABASE IF NOT EXISTS gym_data
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE gym_data;

CREATE TABLE IF NOT EXISTS members (
    member_id INT NOT NULL AUTO_INCREMENT,
    member_name VARCHAR(120) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    birthday DATE NOT NULL,
    age INT NOT NULL,
    membership_type VARCHAR(30) NOT NULL,
    visit_per_week TINYINT UNSIGNED NOT NULL,
    attend_group_lesson BOOLEAN NOT NULL DEFAULT FALSE,
    check_in_time TIME NOT NULL,
    check_out_time TIME NOT NULL,
    avg_time_in_gym_min SMALLINT UNSIGNED NOT NULL,
    drink_addon BOOLEAN NOT NULL DEFAULT FALSE,
    personal_training BOOLEAN NOT NULL DEFAULT FALSE,
    trainer_name VARCHAR(100) NULL,
    uses_sauna BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (member_id),
    INDEX idx_membership_type (membership_type),
    INDEX idx_gender (gender),
    CONSTRAINT chk_member_age CHECK (age BETWEEN 1 AND 120),
    CONSTRAINT chk_visits_per_week CHECK (visit_per_week BETWEEN 0 AND 7),
    CONSTRAINT chk_gym_duration CHECK (avg_time_in_gym_min BETWEEN 0 AND 600)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS member_days (
    day_id INT NOT NULL AUTO_INCREMENT,
    member_id INT NOT NULL,
    day_name VARCHAR(3) NOT NULL,
    PRIMARY KEY (day_id),
    UNIQUE KEY uq_member_day (member_id, day_name),
    CONSTRAINT fk_days_member FOREIGN KEY (member_id)
        REFERENCES members(member_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS member_favorite_lessons (
    lesson_id INT NOT NULL AUTO_INCREMENT,
    member_id INT NOT NULL,
    lesson_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (lesson_id),
    UNIQUE KEY uq_member_lesson (member_id, lesson_name),
    CONSTRAINT fk_lessons_member FOREIGN KEY (member_id)
        REFERENCES members(member_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS member_favorite_drinks (
    drink_id INT NOT NULL AUTO_INCREMENT,
    member_id INT NOT NULL,
    drink_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (drink_id),
    UNIQUE KEY uq_member_drink (member_id, drink_name),
    CONSTRAINT fk_drinks_member FOREIGN KEY (member_id)
        REFERENCES members(member_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
