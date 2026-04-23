// Load .env file if exists
try { require('dotenv').config(); } catch(e) {}

const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 7712;

// Default DB config from environment
const DEFAULT_DB = {
  host: process.env.DB_HOST || '',
  port: process.env.DB_PORT || '',
  database: process.env.DB_DATABASE || '',
  user: process.env.DB_USER || '',
  password: process.env.DB_PASSWORD || '',
};
const HAS_DEFAULT_DB = !!(DEFAULT_DB.host && DEFAULT_DB.database && DEFAULT_DB.user);

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// Connection pool cache (reuse connections per host+db+user)
const pools = {};

function getPoolKey(cfg) {
  return `${cfg.host}:${cfg.port}/${cfg.database}@${cfg.user}`;
}

function getPool(cfg) {
  const key = getPoolKey(cfg);
  if (!pools[key]) {
    pools[key] = new Pool({
      host: cfg.host || 'localhost',
      port: parseInt(cfg.port) || 5432,
      database: cfg.database,
      user: cfg.user,
      password: cfg.password,
      max: 5,
      idleTimeoutMillis: 60000,
      connectionTimeoutMillis: 10000,
    });

    pools[key].on('error', (err) => {
      console.error(`[Pool ${key}] Unexpected error:`, err.message);
      delete pools[key];
    });

    console.log(`[Pool] Created new pool: ${key}`);
  }
  return pools[key];
}

// Merge client config with server defaults (client takes precedence if provided)
function resolveDbConfig(body) {
  return {
    host: body.host || DEFAULT_DB.host,
    port: body.port || DEFAULT_DB.port || 5432,
    database: body.database || DEFAULT_DB.database,
    user: body.user || DEFAULT_DB.user,
    password: (body.password !== undefined && body.password !== '') ? body.password : DEFAULT_DB.password,
  };
}

// ============================================
// GET /api/config/status - Check if server has default DB config
// ============================================
app.get('/api/config/status', (req, res) => {
  res.json({
    hasDefaultDb: HAS_DEFAULT_DB,
    defaults: HAS_DEFAULT_DB ? {
      host: DEFAULT_DB.host,
      port: DEFAULT_DB.port || 5432,
      database: DEFAULT_DB.database,
      user: DEFAULT_DB.user,
    } : null,
  });
});

// ============================================
// POST /api/sql - Execute SQL query
// ============================================
app.post('/api/sql', async (req, res) => {
  const cfg = resolveDbConfig(req.body);
  const { host, port, database, user, password } = cfg;
  const { sql } = req.body;

  // Validate required fields
  if (!sql) {
    return res.status(400).json({ error: 'Missing required field: sql' });
  }
  if (!database) {
    return res.status(400).json({ error: 'Missing database (set DB_DATABASE in .env or send in body)' });
  }
  if (!user) {
    return res.status(400).json({ error: 'Missing user (set DB_USER in .env or send in body)' });
  }

  // Block dangerous statements
  const sqlUpper = sql.trim().toUpperCase();
  const blocked = ['DROP ', 'TRUNCATE ', 'DELETE ', 'ALTER ', 'CREATE ', 'INSERT ', 'UPDATE ', 'GRANT ', 'REVOKE '];
  for (const keyword of blocked) {
    if (sqlUpper.startsWith(keyword)) {
      return res.status(403).json({ error: `Blocked: ${keyword.trim()} statements are not allowed` });
    }
  }

  const startTime = Date.now();

  try {
    const pool = getPool(cfg);
    const result = await pool.query(sql);

    const elapsed = Date.now() - startTime;
    console.log(`[Query] ${database}@${host} | ${result.rowCount} rows | ${elapsed}ms | ${sql.substring(0, 80)}...`);

    res.json({
      data: result.rows,
      rowCount: result.rowCount,
      fields: result.fields.map(f => ({ name: f.name, dataTypeID: f.dataTypeID })),
      elapsed,
    });
  } catch (err) {
    const elapsed = Date.now() - startTime;
    console.error(`[Query Error] ${database}@${host} | ${elapsed}ms | ${err.message}`);

    // Clear pool on auth/connection errors
    if (err.code === '28P01' || err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
      const key = getPoolKey({ host, port, database, user });
      if (pools[key]) {
        pools[key].end().catch(() => {});
        delete pools[key];
      }
    }

    const status = err.code === '28P01' ? 401 : err.code === 'ECONNREFUSED' ? 502 : 500;
    res.status(status).json({
      error: err.message,
      code: err.code,
      elapsed,
    });
  }
});

// ============================================
// GET /api/health - Health check
// ============================================
app.get('/api/health', (req, res) => {
  const poolStats = Object.entries(pools).map(([key, pool]) => ({
    key,
    total: pool.totalCount,
    idle: pool.idleCount,
    waiting: pool.waitingCount,
  }));
  res.json({ status: 'ok', uptime: process.uptime(), pools: poolStats });
});

// ============================================
// GET / - Serve dashboard
// ============================================
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'blb-stock-dashboard.html'));
});

// Start server
app.listen(PORT, () => {
  console.log('');
  console.log('==========================================');
  console.log('  BMS Blood Stock - API Server');
  console.log('==========================================');
  console.log(`  Dashboard : http://localhost:${PORT}`);
  console.log(`  API       : http://localhost:${PORT}/api/sql`);
  console.log(`  Health    : http://localhost:${PORT}/api/health`);
  if (HAS_DEFAULT_DB) {
    console.log(`  Default DB: ${DEFAULT_DB.database}@${DEFAULT_DB.host}:${DEFAULT_DB.port || 5432} (user: ${DEFAULT_DB.user})`);
    console.log(`  >> Client can use API-only mode (Host/DB/User optional)`);
  } else {
    console.log(`  Default DB: (not configured) - client must provide credentials`);
    console.log(`  >> Set DB_HOST, DB_DATABASE, DB_USER, DB_PASSWORD in .env to enable API-only mode`);
  }
  console.log('==========================================');
  console.log('');
});
