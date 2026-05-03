const MAX_POINTS = 30;

function ts() { return new Date().toLocaleTimeString('en-GB', {hour12:false}); }

function addLog(msg, type='') {
  const log = document.getElementById('log');
  if (!log) return;
  const e = document.createElement('div');
  e.className = 'log-entry';
  e.innerHTML = `<span class="log-time">${ts()}</span><span class="log-msg ${type}">${msg}</span>`;
  log.prepend(e);
  if (log.children.length > 100) log.lastChild.remove();
}

function clearLog() { 
  const log = document.getElementById('log');
  if (log) log.innerHTML = ''; 
}

/* Decision log */
let decisionCount = 0;
const ACTION_CLASS = {Scheduled:'scheduled',Preempted:'preempted',Waiting:'waiting',Completed:'completed'};

function addDecision(pid, action) {
  decisionCount++;
  const countEl = document.getElementById('decision-count');
  if (countEl) countEl.textContent = decisionCount + ' decisions';
  
  const log = document.getElementById('decisionLog');
  if (!log) return;
  
  const e = document.createElement('div');
  e.className = 'decision-entry';
  e.innerHTML = `<span class="d-time">${ts()}</span><span class="d-pid">PID ${pid}</span><span class="d-arrow">→</span><span class="d-action ${ACTION_CLASS[action]||''}">${action}</span>`;
  log.prepend(e);
  if (log.children.length > 200) log.lastChild.remove();
}

/* Comparison */
let rlStats = {throughput:0, wait:0};
let rrStats = {throughput:0, wait:0};
let sjfStats = {throughput:0, wait:0};
let fsfsStats = {throughput:0, wait:0};
let priorityStats = {throughput:0, wait:0};

function renderComparison() {
  const update = (id, val) => {
    const el = document.getElementById(id);
    if (el) {
      const num = parseFloat(val) || 0;
      el.textContent = num.toFixed(1);
    }
  };
  
  update('rl-throughput', rlStats.throughput);
  update('rl-wait', rlStats.wait);
  update('rr-throughput', rrStats.throughput);
  update('rr-wait', rrStats.wait);
  update('sjf-throughput', sjfStats.throughput);
  update('sjf-wait', sjfStats.wait);
  update('fsfs-throughput', fsfsStats.throughput);
  update('fsfs-wait', fsfsStats.wait);
  update('priority-throughput', priorityStats.throughput);
  update('priority-wait', priorityStats.wait);

  const maxT = Math.max(rlStats.throughput, rrStats.throughput, sjfStats.throughput, fsfsStats.throughput, priorityStats.throughput, 0.1);
  
  const setBar = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.style.width = ((val/maxT)*100).toFixed(1)+'%';
  };
  
  setBar('rl-bar', rlStats.throughput);
  setBar('rr-bar', rrStats.throughput);
  setBar('sjf-bar', sjfStats.throughput);
  setBar('fsfs-bar', fsfsStats.throughput);
  setBar('priority-bar', priorityStats.throughput);
}

function updateComparison(data) {
  if (data.rl) { 
    rlStats.throughput = parseFloat(data.rl.throughput) || 0; 
    rlStats.wait = parseFloat(data.rl.wait_time) || 0; 
  }
  if (data.rr) { 
    rrStats.throughput = parseFloat(data.rr.throughput) || 0; 
    rrStats.wait = parseFloat(data.rr.wait_time) || 0; 
  }
  if (data.sjf) { 
    sjfStats.throughput = parseFloat(data.sjf.throughput) || 0; 
    sjfStats.wait = parseFloat(data.sjf.wait_time) || 0; 
  }
  if (data.fcfs) { 
    fsfsStats.throughput = parseFloat(data.fcfs.throughput) || 0; 
    fsfsStats.wait = parseFloat(data.fcfs.wait_time) || 0; 
  }
  if (data.priority) { 
    priorityStats.throughput = parseFloat(data.priority.throughput) || 0; 
    priorityStats.wait = parseFloat(data.priority.wait_time) || 0; 
  }
  renderComparison();
}

/* Reward image */
function loadRewardImage(src) {
  const img = document.getElementById('rewardImg');
  const placeholder = document.getElementById('rewardPlaceholder');
  if (img) { img.src = src; img.style.display = 'block'; }
  if (placeholder) placeholder.style.display = 'none';
}

(function(){
  const t = new Image();
  t.onload = () => loadRewardImage('assets/training_curve.png');
  t.src = 'assets/training_curve.png';
})();

/* Stress test */
async function triggerStressTest() {
  const btn = document.getElementById('stressBtn');
  if (!btn) return;
  
  btn.disabled = true; 
  btn.classList.add('active'); 
  btn.textContent = '⚡ RUNNING...';
  addLog('Stress test triggered → POST /api/stress-test', 'warn');
  
  try {
    const res = await fetch('http://localhost:5000/api/stress-test', {method:'POST'});
    addLog(res.ok ? 'Stress test started!' : 'Backend responded: '+res.status, res.ok?'success':'warn');
  } catch(e) {
    addLog('Backend offline — simulating spike locally', 'warn');
  }
  
  setTimeout(() => { 
    btn.disabled=false; 
    btn.classList.remove('active'); 
    btn.textContent='⚡ STRESS TEST'; 
  }, 8000);
}

/* Charts */
function buildDataset(color) {
  return { label:'', data:[], borderColor:color, backgroundColor:color+'18', borderWidth:1.5, pointRadius:0, tension:0.4, fill:true };
}

function buildChart(id, color) {
  const el = document.getElementById(id);
  if (!el) return null;
  
  return new Chart(el.getContext('2d'), {
    type:'line',
    data:{ labels:[], datasets:[buildDataset(color)] },
    options:{
      responsive:true, maintainAspectRatio:false, animation:{duration:200},
      plugins:{legend:{display:false},tooltip:{enabled:false}},
      scales:{
        x:{ticks:{color:'#6b7280',font:{family:'IBM Plex Mono',size:10},maxTicksLimit:6},grid:{color:'#1e2330'}},
        y:{min:0,max:100,ticks:{color:'#6b7280',font:{family:'IBM Plex Mono',size:10},callback:v=>v+'%'},grid:{color:'#1e2330'}}
      }
    }
  });
}

const cpuChart = buildChart('cpuChart','#00e5a0');
const ramChart = buildChart('ramChart','#4f8dff');

function pushPoint(chart, label, value) {
  if (!chart) return;
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  if (chart.data.labels.length > MAX_POINTS) { 
    chart.data.labels.shift(); 
    chart.data.datasets[0].data.shift(); 
  }
  chart.update();
}

/* Metrics */
let prevCpu=null, prevRam=null, prevQueue=null;

function updateMetrics(cpu, ram, queue) {
  try {
    cpu = parseFloat(cpu) || 0;
    ram = parseFloat(ram) || 0;
    queue = parseInt(queue) || 0;
    
    const cpuVal = document.getElementById('cpu-val');
    const cpuBar = document.getElementById('cpu-bar');
    const ramVal = document.getElementById('ram-val');
    const ramBar = document.getElementById('ram-bar');
    const queueVal = document.getElementById('queue-val');
    const queueBar = document.getElementById('queue-bar');
    
    if (cpuVal) cpuVal.textContent = cpu.toFixed(1) + '%';
    if (cpuBar) cpuBar.style.width = cpu + '%';
    
    if (ramVal) ramVal.textContent = ram.toFixed(1) + '%';
    if (ramBar) ramBar.style.width = ram + '%';
    
    if (queueVal) queueVal.textContent = queue;
    if (queueBar) queueBar.style.width = Math.min((queue/50)*100, 100) + '%';
    
    prevCpu = cpu;
    prevRam = ram;
    prevQueue = queue;
  } catch(e) {
    console.error('updateMetrics error:', e);
  }
}

/* Socket.IO */
addLog('Attempting Socket.IO connection...','info');
let socket;

try {
  socket = io('http://localhost:5000', {transports:['websocket'], reconnectionAttempts:5});

  socket.onAny((event, data) => {
  console.log(`[ANY EVENT] ${event}:`, data);
});

  socket.on('connect', () => {
    const el = document.getElementById('conn-status');
    if (el) el.textContent = 'CONNECTED · '+socket.id.slice(0,8);
    addLog('Connected — socket id: '+socket.id,'success');
  });

  socket.on('disconnect', r => { 
    const el = document.getElementById('conn-status');
    if (el) el.textContent='DISCONNECTED'; 
    addLog('Disconnected: '+r,'warn'); 
  });

  socket.on('connect_error', e => { 
    const el = document.getElementById('conn-status');
    if (el) el.textContent='BACKEND OFFLINE'; 
    addLog('Connection error: '+e.message,'warn'); 
  });

  socket.on('resource_update', d => {
    console.log('resource_update:', d);
    const label = ts();
    pushPoint(cpuChart, label, d.cpu_used);
    pushPoint(ramChart, label, d.ram_used);
    updateMetrics(d.cpu_used, d.ram_used, d.queue_length);
    addLog(`cpu=${d.cpu_used.toFixed(1)}% ram=${d.ram_used.toFixed(1)}% q=${d.queue_length}`, 'info');
  });

  socket.on('decision_made', d => {
  console.log('🔥 DECISION_MADE RECEIVED:', d);
  const actionMap = {0:'Scheduled', 1:'Preempted', 2:'Waiting'};
  const pid = d.pid || Math.floor(Math.random() * 900 + 100);
  const action = actionMap[d.action] || 'Unknown';
  console.log('Adding decision - PID:', pid, 'Action:', action);
  addDecision(pid, action);
});

  socket.on('reward_update', d => {
    addLog(`reward: ${d.reward.toFixed(2)}`, 'info');
  });

 socket.on('comparison_update', d => {
  console.log('comparison_update:', d);
  const metrics = {};
  if (d.algos && Array.isArray(d.algos)) {
    for (const algo of d.algos) {
      const name = algo.name.toLowerCase();
      metrics[name] = { 
        throughput: algo.throughput, 
        wait_time: algo.avg_wait 
      };
    }
  }
  updateComparison(metrics);
  
  // Throttle chart updates
  const now = Date.now();
  if (now - lastChartUpdate < CHART_UPDATE_INTERVAL) return;
  lastChartUpdate = now;
  
  if (d.algos && Array.isArray(d.algos)) {
    const rlAlgo = d.algos.find(a => a.name.toLowerCase() === 'rl');
    if (rlAlgo) {
      const cpu = Math.min(rlAlgo.cpu || 30, 100);
      const ram = Math.min(rlAlgo.ram || 30, 100);
      const queue = rlAlgo.queue || 0;
      const label = ts();
      pushPoint(cpuChart, label, cpu);
      pushPoint(ramChart, label, ram);
      updateMetrics(cpu, ram, queue);
    }
  }
});

  socket.on('reward_image', d => { 
    loadRewardImage(d.path); 
    addLog('Training curve loaded','success'); 
  });

  socket.onAny((event, ...a) => { 
    if (!['resource_update','decision_made','reward_update','comparison_update','reward_image'].includes(event)) 
      console.log(`[EVENT] ${event}:`, a); 
  });

} catch(e) { 
  addLog('Socket.IO init failed: '+e.message,'warn'); 
  console.error(e);
}

renderComparison();