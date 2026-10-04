CREATE DATABASE IF NOT EXISTS autoservice_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE autoservice_db;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE application_statuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);


CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_type VARCHAR(255) NOT NULL,
    car_model VARCHAR(100) NOT NULL,
    vin VARCHAR(17) NOT NULL,
    start_date DATE NOT NULL,
    payment_method_id INT NOT NULL,
    status_id INT NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id),
    FOREIGN KEY (status_id) REFERENCES application_statuses(id),
    UNIQUE(user_id, vin, start_date) -- Защита от дубликатов по варианту
);

CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


INSERT INTO roles (name) VALUES ('Гость'), ('Пользователь'), ('Администратор');
INSERT INTO payment_methods (name) VALUES ('Наличные'), ('Банковская карта'), ('СБП');
INSERT INTO application_statuses (name) VALUES ('Новая'), ('В работе'), ('Ремонт завершен');


INSERT INTO users (login, password_hash, full_name, phone, email, role_id) 
VALUES ('Admin', 'scrypt:32768:8:1$yX8w...$', 'Администратор', '8(999)999-99-99', 'admin@auto.ru', 3);