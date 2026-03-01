-- BookTok Database Schema for MariaDB

CREATE DATABASE IF NOT EXISTS ellen_booktok
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ellen_booktok;

-- Books
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(300) NOT NULL,
    cover_image VARCHAR(1000),
    description TEXT,
    isbn VARCHAR(13),
    google_books_id VARCHAR(50),
    average_rating DECIMAL(3, 2) DEFAULT 0.00,
    total_reviews INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_title (title(100)),
    INDEX idx_author (author(100)),
    INDEX idx_isbn (isbn)
) ENGINE=InnoDB;

-- Tropes
CREATE TABLE tropes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slug (slug)
) ENGINE=InnoDB;

-- Book <-> Trope (many-to-many)
CREATE TABLE book_tropes (
    book_id INT NOT NULL,
    trope_id INT NOT NULL,
    PRIMARY KEY (book_id, trope_id),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (trope_id) REFERENCES tropes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Trending data (one row per book per day per platform)
CREATE TABLE trending_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    date DATE NOT NULL,
    mention_count INT DEFAULT 0,
    sentiment_score DECIMAL(3, 2) DEFAULT 0.00,
    trending_score DECIMAL(8, 2) DEFAULT 0.00,
    platform VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    INDEX idx_book_date (book_id, date),
    INDEX idx_date_platform (date, platform),
    INDEX idx_trending (trending_score DESC)
) ENGINE=InnoDB;

-- Users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- Reviews
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    rating TINYINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_book (user_id, book_id),
    INDEX idx_book (book_id)
) ENGINE=InnoDB;

-- Reading lists
CREATE TABLE reading_lists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB;

-- Raw social media posts (before AI processing)
CREATE TABLE raw_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    platform_id VARCHAR(200) NOT NULL UNIQUE,
    author VARCHAR(200),
    text TEXT,
    hashtags JSON,
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    url VARCHAR(1000),
    posted_at TIMESTAMP NULL,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed TINYINT DEFAULT 0,
    INDEX idx_platform (platform),
    INDEX idx_processed (processed),
    INDEX idx_collected (collected_at)
) ENGINE=InnoDB;

-- Reading list <-> Book (many-to-many)
CREATE TABLE reading_list_books (
    reading_list_id INT NOT NULL,
    book_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (reading_list_id, book_id),
    FOREIGN KEY (reading_list_id) REFERENCES reading_lists(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
) ENGINE=InnoDB;
