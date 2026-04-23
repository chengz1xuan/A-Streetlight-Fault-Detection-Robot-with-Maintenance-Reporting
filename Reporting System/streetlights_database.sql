-- 1. 创建数据库
CREATE DATABASE streetlight_db;
USE streetlight_db;

-- 2. 创建维修人员表
CREATE TABLE workers (
    worker_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_name VARCHAR(50) NOT NULL,
    email VARCHAR(50)
);

-- 3. 创建路灯记录表
CREATE TABLE streetlight_records (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- 路灯编号，例如 LAMP001
    lamp_id VARCHAR(10) NOT NULL,

    -- GPS 坐标，例如 "37.12345,122.98765"
    gps VARCHAR(50) NOT NULL,

    -- 路灯状态：off / dim / covered / on
    status VARCHAR(10) NOT NULL,

    -- 图片绝对路径
    file_path VARCHAR(200) NOT NULL,

    -- 分配的维修人员，对应 workers.worker_id
    repair_worker INT DEFAULT NULL,

    -- 维修状态
    repair_status ENUM('Pending', 'Received', 'Processing', 'Completed', 'Fail') DEFAULT 'Pending',

    -- 记录创建时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    CONSTRAINT fk_worker FOREIGN KEY (repair_worker)
    REFERENCES workers(worker_id)
);

-- 4. 插入维修人员数据
INSERT INTO workers (worker_id, worker_name, email)
VALUES
(1, 'Jack', '1235442@wku.edu.cn'),
(2, 'Bob', 'chenzixu@kean.edu'),
(3, 'Lee', '2369488481@qq.com');

-- 5. 如果旧数据里 repair_worker 还是字符串形式，可先临时关闭安全更新
SET SQL_SAFE_UPDATES = 0;

UPDATE streetlight_records SET repair_worker = 1 WHERE repair_worker = 'worker_1';
UPDATE streetlight_records SET repair_worker = 2 WHERE repair_worker = 'worker_2';
UPDATE streetlight_records SET repair_worker = 3 WHERE repair_worker = 'worker_3';

SET SQL_SAFE_UPDATES = 1;

-- 6. 查看表结构
DESCRIBE streetlight_records;

-- 7. 清空数据并重置自增ID
DELETE FROM streetlight_records;
ALTER TABLE streetlight_records AUTO_INCREMENT = 1;