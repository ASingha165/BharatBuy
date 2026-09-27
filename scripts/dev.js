#!/usr/bin/env node

/**
 * BharatBuy Local Development Launcher
 * 
 * Canonical development command:
 *   npm run dev
 * 
 * Starts both:
 *   - FastAPI / Uvicorn Backend on http://localhost:8000
 *   - Next.js Frontend on http://localhost:3000
 * 
 * Features:
 *   - Zero npm dependencies (pure Node.js standard library)
 *   - Pre-flight port conflict check (ports 3000 & 8000) with owning process reporting
 *   - Automatic detection of clean Python venv (backend/.venv_clean/Scripts/python.exe)
 *   - Backend startup health check polling (http://localhost:8000/api/v1/health)
 *   - Graceful shutdown handling (SIGINT / SIGTERM / exit) with process tree cleanup
 *   - Colorized output streaming for [FRONTEND] and [BACKEND]
 */

const { spawn, execSync } = require('child_process');
const http = require('http');
const net = require('net');
const path = require('path');
const fs = require('fs');

const ROOT_DIR = path.resolve(__dirname, '..');
const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend');
const BACKEND_DIR = path.join(ROOT_DIR, 'backend');

const FRONTEND_PORT = 3000;
const BACKEND_PORT = 8000;
const HEALTH_CHECK_URL = `http://127.0.0.1:${BACKEND_PORT}/api/v1/health`;
const HEALTH_CHECK_MAX_ATTEMPTS = 40; // 20 seconds max (40 * 500ms)
const HEALTH_CHECK_INTERVAL_MS = 500;

// ANSI Colors
const CYAN = '\x1b[36m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const RED = '\x1b[31m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';

let backendProcess = null;
let frontendProcess = null;
let isShuttingDown = false;
let healthCheckTimer = null;

/**
 * Find the process owning a specific TCP port
 */
function getProcessForPort(port) {
  if (process.platform === 'win32') {
    try {
      const netstatOutput = execSync('netstat -ano -p tcp', {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'ignore']
      });
      const lines = netstatOutput.split('\n');
      for (const line of lines) {
        if ((line.includes(`:${port} `) || line.includes(`:${port}\t`)) && line.includes('LISTENING')) {
          const parts = line.trim().split(/\s+/);
          const pid = parts[parts.length - 1];
          if (pid && !isNaN(parseInt(pid, 10))) {
            let procName = 'Unknown';
            try {
              const taskOutput = execSync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`, {
                encoding: 'utf8',
                stdio: ['pipe', 'pipe', 'ignore']
              });
              const match = taskOutput.match(/^"([^"]+)"/);
              if (match) procName = match[1];
            } catch (e) {}
            return { pid: parseInt(pid, 10), procName };
          }
        }
      }
    } catch (e) {}
  } else {
    try {
      const lsofOutput = execSync(`lsof -i :${port} -sTCP:LISTEN -t`, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'ignore']
      }).trim();
      if (lsofOutput) {
        const pid = parseInt(lsofOutput.split('\n')[0], 10);
        let procName = 'Unknown';
        try {
          procName = execSync(`ps -p ${pid} -o comm=`, {
            encoding: 'utf8',
            stdio: ['pipe', 'pipe', 'ignore']
          }).trim();
        } catch (e) {}
        return { pid, procName };
      }
    } catch (e) {}
  }
  return null;
}

/**
 * Check if a TCP port is currently in use
 */
function checkPortInUse(port) {
  // First, check active OS listening sockets
  const proc = getProcessForPort(port);
  if (proc) return Promise.resolve(true);

  // Fallback to socket test
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    server.once('listening', () => {
      server.close(() => {
        resolve(false);
      });
    });
    server.listen(port);
  });
}

/**
 * Locate the appropriate clean Python executable
 */
function resolvePythonExecutable() {
  const candidates = [
    // Windows clean venv (SIH26108 designated)
    path.join(BACKEND_DIR, '.venv_clean', 'Scripts', 'python.exe'),
    // POSIX clean venv
    path.join(BACKEND_DIR, '.venv_clean', 'bin', 'python'),
    // Fallback standard venv
    path.join(BACKEND_DIR, '.venv', 'Scripts', 'python.exe'),
    path.join(BACKEND_DIR, '.venv', 'bin', 'python'),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  // System fallback
  return process.platform === 'win32' ? 'python.exe' : 'python3';
}

/**
 * Kill a process and its entire child process tree
 */
function killProcessTree(child) {
  if (!child || !child.pid) return;

  if (process.platform === 'win32') {
    try {
      execSync(`taskkill /PID ${child.pid} /T /F`, { stdio: 'ignore' });
    } catch (e) {
      // Process already terminated
    }
  } else {
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch (e) {
      try {
        child.kill('SIGTERM');
      } catch (err) {}
    }
  }
}

/**
 * Clean shutdown handler
 */
function shutdown(signal) {
  if (isShuttingDown) return;
  isShuttingDown = true;

  if (healthCheckTimer) {
    clearTimeout(healthCheckTimer);
    healthCheckTimer = null;
  }

  console.log(`\n${YELLOW}[DEV LAUNCHER] Received ${signal || 'shutdown signal'}, stopping all services gracefully...${RESET}`);

  if (backendProcess) {
    console.log(`${CYAN}[DEV LAUNCHER] Stopping FastAPI backend (PID ${backendProcess.pid})...${RESET}`);
    killProcessTree(backendProcess);
    backendProcess = null;
  }

  if (frontendProcess) {
    console.log(`${GREEN}[DEV LAUNCHER] Stopping Next.js frontend (PID ${frontendProcess.pid})...${RESET}`);
    killProcessTree(frontendProcess);
    frontendProcess = null;
  }

  console.log(`${GREEN}[DEV LAUNCHER] All development services stopped cleanly.${RESET}`);
  process.exit(0);
}

// Register process exit listeners
process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGHUP', () => shutdown('SIGHUP'));
process.on('exit', () => {
  if (!isShuttingDown) {
    killProcessTree(backendProcess);
    killProcessTree(frontendProcess);
  }
});

/**
 * Poll backend health endpoint until 200 OK or timeout
 */
function pollBackendHealth(attempt = 1) {
  if (isShuttingDown) return;

  const req = http.get(HEALTH_CHECK_URL, { timeout: 2000 }, (res) => {
    let body = '';
    res.on('data', (chunk) => { body += chunk; });
    res.on('end', () => {
      if (res.statusCode === 200) {
        try {
          const data = JSON.parse(body);
          printHealthSuccessBanner(data);
        } catch (e) {
          printHealthSuccessBanner({ status: 'healthy', total_standards: 559 });
        }
      } else if (attempt < HEALTH_CHECK_MAX_ATTEMPTS) {
        healthCheckTimer = setTimeout(() => pollBackendHealth(attempt + 1), HEALTH_CHECK_INTERVAL_MS);
      } else {
        console.warn(`${YELLOW}[DEV LAUNCHER WARNING] Backend returned HTTP ${res.statusCode} at ${HEALTH_CHECK_URL}${RESET}`);
      }
    });
  });

  req.on('error', () => {
    if (attempt < HEALTH_CHECK_MAX_ATTEMPTS && !isShuttingDown) {
      healthCheckTimer = setTimeout(() => pollBackendHealth(attempt + 1), HEALTH_CHECK_INTERVAL_MS);
    } else if (!isShuttingDown) {
      console.warn(`${YELLOW}[DEV LAUNCHER WARNING] Backend health check timed out after ${HEALTH_CHECK_MAX_ATTEMPTS * HEALTH_CHECK_INTERVAL_MS / 1000}s. Check logs above.${RESET}`);
    }
  });

  req.on('timeout', () => {
    req.destroy();
    if (attempt < HEALTH_CHECK_MAX_ATTEMPTS && !isShuttingDown) {
      healthCheckTimer = setTimeout(() => pollBackendHealth(attempt + 1), HEALTH_CHECK_INTERVAL_MS);
    }
  });
}

function printHealthSuccessBanner(data) {
  console.log(`
${GREEN}========================================================================${RESET}
${GREEN}${BOLD}✓ BHARATBUY LOCAL DEVELOPMENT ENVIRONMENT IS ACTIVE${RESET}
${GREEN}------------------------------------------------------------------------${RESET}
  ${BOLD}Frontend Application:${RESET}  http://localhost:${FRONTEND_PORT}
  ${BOLD}Backend REST API:${RESET}      http://localhost:${BACKEND_PORT}/api/v1
  ${BOLD}Backend Health Status:${RESET} http://localhost:${BACKEND_PORT}/api/v1/health [Status: ${data.status || 'healthy'}]
  ${BOLD}Interactive API Docs:${RESET}  http://localhost:${BACKEND_PORT}/api/v1/docs
  ${BOLD}Standards Database:${RESET}    ${data.total_standards || 559} Indian Standards active
  ${BOLD}Model Strategy:${RESET}        ${data.model_type || 'baseline'} (Hybrid BM25 + Vector)
  ${BOLD}AI Provider:${RESET}           ${data.gemini_configured ? 'Gemini Active' : 'Deterministic Technical Fallback'}
  ${BOLD}Environment Mode:${RESET}      ${data.is_demo_mode ? 'Demo Mode' : 'Production Registry'}
${GREEN}------------------------------------------------------------------------${RESET}
  Press ${BOLD}Ctrl+C${RESET} in this terminal to stop both Frontend and Backend servers.
${GREEN}========================================================================${RESET}
`);
}

/**
 * Pipe child process logs with tagged color prefixes
 */
function attachProcessLogger(child, prefix, color) {
  const lineReader = (stream, isError = false) => {
    let buffer = '';
    stream.on('data', (chunk) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Retain incomplete line
      for (const line of lines) {
        if (line.trim().length > 0) {
          const tag = `${color}[${prefix}]${RESET}`;
          if (isError) {
            console.error(`${tag} ${line}`);
          } else {
            console.log(`${tag} ${line}`);
          }
        }
      }
    });
    stream.on('end', () => {
      if (buffer.trim().length > 0) {
        const tag = `${color}[${prefix}]${RESET}`;
        if (isError) {
          console.error(`${tag} ${buffer}`);
        } else {
          console.log(`${tag} ${buffer}`);
        }
      }
    });
  };

  if (child.stdout) lineReader(child.stdout, false);
  if (child.stderr) lineReader(child.stderr, true);
}

/**
 * Main startup orchestrator
 */
async function main() {
  console.log(`${BOLD}${CYAN}=== BHARATBUY LOCAL DEVELOPMENT LAUNCHER ===${RESET}`);
  console.log(`Working Directory: ${ROOT_DIR}\n`);

  // 1. Pre-flight Port Conflict Check
  console.log(`Checking port availability (Frontend: ${FRONTEND_PORT}, Backend: ${BACKEND_PORT})...`);
  const frontendInUse = await checkPortInUse(FRONTEND_PORT);
  const backendInUse = await checkPortInUse(BACKEND_PORT);

  if (frontendInUse || backendInUse) {
    console.error(`\n${RED}${BOLD}[PORT CONFLICT ERROR]${RESET} Cannot start development servers:`);
    const frontProc = getProcessForPort(FRONTEND_PORT);
    const backProc = getProcessForPort(BACKEND_PORT);

    if (frontendInUse) {
      const detail = frontProc ? `occupied by PID ${frontProc.pid} (${frontProc.procName})` : 'occupied by an existing process';
      console.error(`  - Port ${FRONTEND_PORT} (Frontend) is ${RED}${detail}${RESET}`);
    }
    if (backendInUse) {
      const detail = backProc ? `occupied by PID ${backProc.pid} (${backProc.procName})` : 'occupied by an existing process';
      console.error(`  - Port ${BACKEND_PORT} (Backend) is ${RED}${detail}${RESET}`);
    }

    console.error(`\n${YELLOW}Please stop the conflicting process(es) before running 'npm run dev':${RESET}`);
    if (process.platform === 'win32') {
      if (frontProc) console.error(`  taskkill /F /PID ${frontProc.pid}`);
      if (backProc) console.error(`  taskkill /F /PID ${backProc.pid}`);
    } else {
      if (frontProc) console.error(`  kill -9 ${frontProc.pid}`);
      if (backProc) console.error(`  kill -9 ${backProc.pid}`);
    }
    console.error('');
    process.exit(1);
  }

  console.log(`${GREEN}✓ Ports ${FRONTEND_PORT} and ${BACKEND_PORT} are available.${RESET}\n`);

  // 2. Resolve Python environment
  const pythonExe = resolvePythonExecutable();
  console.log(`Python Environment: ${pythonExe}`);
  if (!fs.existsSync(pythonExe)) {
    console.error(`${RED}[ERROR] Python executable not found at: ${pythonExe}${RESET}`);
    console.error(`Please verify backend virtual environment exists.`);
    process.exit(1);
  }

  // 3. Start Backend: FastAPI / Uvicorn on port 8000
  console.log(`${CYAN}[BACKEND] Starting FastAPI on http://127.0.0.1:${BACKEND_PORT}...${RESET}`);
  const backendArgs = [
    '-m', 'uvicorn',
    'backend.app.main:app',
    '--host', '127.0.0.1',
    '--port', String(BACKEND_PORT),
    '--reload'
  ];

  const backendEnv = {
    ...process.env,
    PYTHONUNBUFFERED: '1',
    PORT: String(BACKEND_PORT),
    HOST: '127.0.0.1',
  };

  backendProcess = spawn(pythonExe, backendArgs, {
    cwd: ROOT_DIR,
    env: backendEnv,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  attachProcessLogger(backendProcess, 'BACKEND', CYAN);

  backendProcess.on('error', (err) => {
    console.error(`${RED}[BACKEND ERROR] Failed to spawn FastAPI server:${RESET}`, err);
    shutdown('BACKEND_CRASH');
  });

  backendProcess.on('exit', (code, signal) => {
    if (!isShuttingDown) {
      console.error(`${RED}[BACKEND EXITED] FastAPI server stopped unexpectedly (code: ${code}, signal: ${signal})${RESET}`);
      shutdown('BACKEND_EXIT');
    }
  });

  // 4. Start Frontend: Next.js on port 3000
  console.log(`${GREEN}[FRONTEND] Starting Next.js on http://localhost:${FRONTEND_PORT}...${RESET}`);
  const isWin = process.platform === 'win32';
  
  // On Windows, run cmd.exe /c npm run dev to avoid shell:true deprecation warning
  const frontendCmd = isWin ? 'cmd.exe' : 'npm';
  const frontendArgs = isWin ? ['/c', 'npm', 'run', 'dev'] : ['run', 'dev'];

  const frontendEnv = {
    ...process.env,
    PORT: String(FRONTEND_PORT),
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || `http://127.0.0.1:${BACKEND_PORT}/api/v1`,
  };

  frontendProcess = spawn(frontendCmd, frontendArgs, {
    cwd: FRONTEND_DIR,
    env: frontendEnv,
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: false
  });

  attachProcessLogger(frontendProcess, 'FRONTEND', GREEN);

  frontendProcess.on('error', (err) => {
    console.error(`${RED}[FRONTEND ERROR] Failed to spawn Next.js dev server:${RESET}`, err);
    shutdown('FRONTEND_CRASH');
  });

  frontendProcess.on('exit', (code, signal) => {
    if (!isShuttingDown) {
      console.error(`${RED}[FRONTEND EXITED] Next.js dev server stopped (code: ${code}, signal: ${signal})${RESET}`);
      shutdown('FRONTEND_EXIT');
    }
  });

  // 5. Begin Backend Health Check Polling
  setTimeout(() => {
    pollBackendHealth(1);
  }, 1000);
}

main().catch((err) => {
  console.error(`${RED}[FATAL ERROR] Launcher encountered an unhandled exception:${RESET}`, err);
  shutdown('FATAL_ERROR');
});
