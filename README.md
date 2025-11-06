# plant_disease_detection

install python version 3.10.11 in your system before running this file. 

create a my sql database on xampp: 
run below commands:

CREATE DATABSE plant_system;

USE DATABASE plant_system;

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL
) 

CREATE TABLE `classification_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `disease_name` varchar(100) DEFAULT NULL,
  `probability` decimal(5,2) DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) 

after creating the database. run app.py in your desierd code editor. the port no will be in the terminal, click on the link to go to the localhost page. from the you will be able to use the system properly. 
