-- AI-Agent 数据库初始化 SQL
-- 使用方法: mysql -u root -p < init_database.sql

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `ai_agent`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 创建用户（请修改密码）
-- 将 'your_password_here' 替换为你的实际密码
CREATE USER IF NOT EXISTS 'ai_agent'@'localhost' IDENTIFIED BY 'your_password_here';

-- 授予权限
GRANT ALL PRIVILEGES ON `ai_agent`.* TO 'ai_agent'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示用户权限（验证）
SHOW GRANTS FOR 'ai_agent'@'localhost';

-- 使用数据库
USE `ai_agent`;

-- 显示数据库信息
SELECT
    'Database created successfully!' AS status,
    DATABASE() AS current_database,
    VERSION() AS mysql_version;
