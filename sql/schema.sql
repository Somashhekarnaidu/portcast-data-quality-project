CREATE DATABASE IF NOT EXISTS portcast_data_quality;
USE portcast_data_quality;

-- main.py creates/replaces these two tables when MYSQL_URL is configured.
-- This file creates the database. Do not use real customer or confidential data.

CREATE TABLE IF NOT EXISTS project_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    note_text VARCHAR(255) NOT NULL
);

INSERT INTO project_notes (note_text)
VALUES ('Demo project: validate shipment data before downstream analysis');
