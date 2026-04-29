/* ── Helpers ── */
    const MAX_POINTS = 30;

    function ts() {
      return new Date().toLocaleTimeString('en-GB', { hour12: false });
    }

    function addLog(msg, type = '') {
      const log = document.getElementById('log');
      const entry = document.createElement('div');
      entry.className = 'log-entry';
      entry.innerHTML = `<span class="log-time">${ts()}</span><span class="log-msg ${type}">${msg}</span>`;
      log.prepend(entry);
      if (log.children.length > 100) log.lastChild.remove();
    }

    function clearLog() {
      document.getElementById('log').innerHTML = '';
    }

    function buildDataset(color) {
      return {
        label: '',
        data: [],
        borderColor: color,
        backgroundColor: color + '18',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.4,
        fill: true,
      };
    }

    function buildChart(id, color) {
      const ctx = document.getElementById(id).getContext('2d');
      return new Chart(ctx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [buildDataset(color)]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 200 },
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: {
            x: {
              ticks: { color: '#6b7280', font: { family: 'IBM Plex Mono', size: 10 }, maxTicksLimit: 6 },
              grid: { color: '#1e2330' }
            },
            y: {
              min: 0, max: 100,
              ticks: {
                color: '#6b7280',
                font: { family: 'IBM Plex Mono', size: 10 },
                callback: v => v + '%'
              },
              grid: { color: '#1e2330' }
            }
          }
        }
      });
    }

    /* ── Charts ── */
    const cpuChart = buildChart('cpuChart', '#00e5a0');
    const ramChart = buildChart('ramChart', '#4f8dff');

    function pushPoint(chart, label, value) {
      chart.data.labels.push(label);
      chart.data.datasets[0].data.push(value);
      if (chart.data.labels.length > MAX_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
      }
      chart.update();
    }

    /* ── Metric card update ── */
    let prevCpu = null, prevRam = null, prevQueue = null;

    function updateMetrics(cpu, ram, queue) {
      document.getElementById('cpu-val').textContent = cpu.toFixed(1) + '%';
      document.getElementById('cpu-bar').style.width = cpu + '%';
      if (prevCpu !== null) {
        const d = (cpu - prevCpu).toFixed(1);
        document.getElementById('cpu-delta').textContent = (d >= 0 ? '▲ +' : '▼ ') + d + '% from last';
      }
      prevCpu = cpu;

      document.getElementById('ram-val').textContent = ram.toFixed(1) + '%';
      document.getElementById('ram-bar').style.width = ram + '%';
      if (prevRam !== null) {
        const d = (ram - prevRam).toFixed(1);
        document.getElementById('ram-delta').textContent = (d >= 0 ? '▲ +' : '▼ ') + d + '% from last';
      }
      prevRam = ram;

      const qpct = Math.min((queue / 50) * 100, 100);
      document.getElementById('queue-val').textContent = queue;
      document.getElementById('queue-bar').style.width = qpct + '%';
      if (prevQueue !== null) {
        const d = queue - prevQueue;
        document.getElementById('queue-delta').textContent = (d >= 0 ? '▲ +' : '▼ ') + d + ' tasks from last';
      }
      prevQueue = queue;
    }

    /* ── Socket.IO ── */
    addLog('Attempting Socket.IO connection to backend...', 'info');

    let socket;
    try {
      socket = io('http://localhost:5000', { transports: ['websocket'], reconnectionAttempts: 5 });

      socket.on('connect', () => {
        document.getElementById('conn-status').textContent = 'CONNECTED · ' + socket.id.slice(0, 8);
        addLog('Connected — socket id: ' + socket.id, 'success');
      });

      socket.on('disconnect', reason => {
        document.getElementById('conn-status').textContent = 'DISCONNECTED';
        addLog('Disconnected — reason: ' + reason, 'warn');
      });

      socket.on('connect_error', err => {
        document.getElementById('conn-status').textContent = 'BACKEND OFFLINE (DEMO MODE)';
        addLog('Connection error: ' + err.message, 'warn');
      });

      /* ─ Main data event: backend emits { cpu, ram, queue, timestamp } ─ */
      socket.on('metrics', data => {
        addLog(`metrics → cpu=${data.cpu.toFixed(1)}% ram=${data.ram.toFixed(1)}% q=${data.queue}`, 'info');
        const label = data.timestamp || ts();
        pushPoint(cpuChart, label, data.cpu);
        pushPoint(ramChart, label, data.ram);
        updateMetrics(data.cpu, data.ram, data.queue);
      });

      /* ─ Listen for any extra events and log them ─ */
      socket.onAny((event, ...args) => {
        if (event !== 'metrics') addLog(`event: ${event} → ${JSON.stringify(args)}`, 'info');
      });

    } catch (e) {
      addLog('Socket.IO init failed: ' + e.message, 'warn');
    }

    /* ── Demo mode: simulate data when backend is offline ── */
    let demoCpu = 30, demoRam = 45, demoQueue = 5;

    setInterval(() => {
      if (!socket || !socket.connected) {
        demoCpu  = Math.max(5,  Math.min(95, demoCpu  + (Math.random() - 0.48) * 6));
        demoRam  = Math.max(20, Math.min(90, demoRam  + (Math.random() - 0.48) * 4));
        demoQueue = Math.max(0, Math.min(50, demoQueue + Math.round((Math.random() - 0.5) * 3)));
        const label = ts();
        pushPoint(cpuChart, label, +demoCpu.toFixed(1));
        pushPoint(ramChart, label, +demoRam.toFixed(1));
        updateMetrics(demoCpu, demoRam, demoQueue);
        addLog(`[demo] cpu=${demoCpu.toFixed(1)}% ram=${demoRam.toFixed(1)}% q=${demoQueue}`, 'info');
      }
    }, 1500);