# Resource-Constrained VM Tuning Guide (2-Core / 2GB RAM)

## Overview
When deploying a Koa + Node.js backend alongside MySQL on a small virtual machine (2 vCPUs, 2GB RAM), resource contention between Node processes and the database engine is the primary cause of latency degradation. This guide defines optimal configurations.

---

## 1. System Resource Contention Architecture

```text
               2 vCPUs / 2GB RAM Host
                         │
        ┌────────────────┴────────────────┐
        │                                 │
 Node.js Runtime                  MySQL 8.0 Engine
 (PM2 Cluster: 1 or 2 Workers)    (InnoDB Buffer Pool)
 ~500MB RAM                       ~1000MB RAM
```

If Node.js and MySQL compete for memory, the host kernel triggers swap thrashing or OOM killer events, increasing API latency from 200ms to 4000ms.

---

## 2. PM2 Worker Optimization: 1 vs. 2 Workers

Do not blindly assume that `pm2 start -i max` or 2 cluster workers is always faster on a 2-core host:
- **PM2 with 2 Workers**:
  - Each worker consumes ~200–300MB RAM.
  - Doubled MySQL connection pool count.
  - Context switching overhead between 2 Node workers, MySQL threads, and OS processes.
- **PM2 with 1 Worker (Fork Mode)**:
  - Conserves ~250MB RAM for MySQL InnoDB buffer pool.
  - Eliminates inter-process IPC overhead.

### Empirical Benchmarking Protocol
Before finalizing deployment, benchmark both configurations using k6:
```bash
# Benchmark 1 worker
pm2 restart app --instances 1
k6 run tests/performance/k6-load-suite.js

# Benchmark 2 workers
pm2 restart app --instances 2
k6 run tests/performance/k6-load-suite.js
```
*Rule of Thumb*: If 1 worker yields lower $p95$ and zero error rate, keep 1 worker on 2GB hosts.

---

## 3. MySQL Connection Pool Sizing

Default pool sizes of 50–100 connections will exhaust memory and lock MySQL on low-spec VMs:

```javascript
// src/database.js
const { Sequelize } = require('sequelize');

const sequelize = new Sequelize(dbName, dbUser, dbPass, {
  dialect: 'mysql',
  pool: {
    max: 10,       // Never exceed 10 connections per Node process on 2GB RAM
    min: 2,        // Keep warm connections ready
    acquire: 15000,// 15s timeout before throwing ConnectionAcquireTimeout
    idle: 5000,    // Release inactive connections after 5s
  },
});

module.exports = { sequelize };
```

---

## 4. MySQL InnoDB Buffer Pool Configuration
In `/etc/mysql/my.cnf`:
```ini
[mysqld]
# On a 2GB VM, allocate 500M-750M to InnoDB buffer pool
innodb_buffer_pool_size = 600M
innodb_log_file_size = 128M
max_connections = 50
table_open_cache = 400
```

---

## 5. Monitoring Diagnostics
Execute these commands during k6 load testing:
```bash
# Check CPU & RAM saturation
htop

# Inspect MySQL active query threads
mysql -e "SHOW PROCESSLIST;"

# Inspect Node event loop delay
node -e "const { monitorEventLoopDelay } = require('perf_hooks'); const h = monitorEventLoopDelay(); h.enable(); setTimeout(() => console.log('p95 event loop lag:', h.percentile(95) / 1e6, 'ms'), 5000);"
```
