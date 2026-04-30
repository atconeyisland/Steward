const MAX_POINTS = 30;

    function ts() { return new Date().toLocaleTimeString('en-GB', {hour12:false}); }

    function addLog(msg, type='') {
      const log = document.getElementById('log');
      const e = document.createElement('div');
      e.className = 'log-entry';
      e.innerHTML = `<span class="log-time">${ts()}</span><span class="log-msg ${type}">${msg}</span>`;
      log.prepend(e);
      if (log.children.length > 100) log.lastChild.remove();
    }
    function clearLog() { document.getElementById('log').innerHTML = ''; }

    /* Decision log */
    let decisionCount = 0;
    const ACTION_CLASS = {Scheduled:'scheduled',Preempted:'preempted',Waiting:'waiting',Completed:'completed'};

    function addDecision(pid, action) {
      decisionCount++;
      document.getElementById('decision-count').textContent = decisionCount + ' decisions';
      const log = document.getElementById('decisionLog');
      const e = document.createElement('div');
      e.className = 'decision-entry';
      e.innerHTML = `<span class="d-time">${ts()}</span><span class="d-pid">PID ${pid}</span><span class="d-arrow">→</span><span class="d-action ${ACTION_CLASS[action]||''}">${action}</span>`;
      log.prepend(e);
      if (log.children.length > 200) log.lastChild.remove();
    }

    /* Comparison */
    let rlStats = {throughput:8.2, wait:14.3};
let rrStats = {throughput:5.6, wait:22.8};
let sjfStats = {throughput:6.1, wait:18.9};
let fsfsStats = {throughput:4.8, wait:26.2};
let priorityStats = {throughput:7.3, wait:16.5};

    function renderComparison() {
  document.getElementById('rl-throughput').textContent = rlStats.throughput.toFixed(1) + ' tasks/s';
  document.getElementById('rl-wait').textContent = rlStats.wait.toFixed(1) + ' ms';
  
  document.getElementById('rr-throughput').textContent = rrStats.throughput.toFixed(1) + ' tasks/s';
  document.getElementById('rr-wait').textContent = rrStats.wait.toFixed(1) + ' ms';
  
  document.getElementById('sjf-throughput').textContent = sjfStats.throughput.toFixed(1) + ' tasks/s';
  document.getElementById('sjf-wait').textContent = sjfStats.wait.toFixed(1) + ' ms';
  
  document.getElementById('fsfs-throughput').textContent = fsfsStats.throughput.toFixed(1) + ' tasks/s';
  document.getElementById('fsfs-wait').textContent = fsfsStats.wait.toFixed(1) + ' ms';
  
  document.getElementById('priority-throughput').textContent = priorityStats.throughput.toFixed(1) + ' tasks/s';
  document.getElementById('priority-wait').textContent = priorityStats.wait.toFixed(1) + ' ms';

  const maxT = Math.max(rlStats.throughput, rrStats.throughput, sjfStats.throughput, fsfsStats.throughput, priorityStats.throughput, 0.1);
  document.getElementById('rl-bar').style.width = ((rlStats.throughput/maxT)*100).toFixed(1)+'%';
  document.getElementById('rr-bar').style.width = ((rrStats.throughput/maxT)*100).toFixed(1)+'%';
  document.getElementById('sjf-bar').style.width = ((sjfStats.throughput/maxT)*100).toFixed(1)+'%';
  document.getElementById('fsfs-bar').style.width = ((fsfsStats.throughput/maxT)*100).toFixed(1)+'%';
  document.getElementById('priority-bar').style.width = ((priorityStats.throughput/maxT)*100).toFixed(1)+'%';
}

function updateComparison(data) {
  if (data.rl) { rlStats.throughput = data.rl.throughput ?? rlStats.throughput; rlStats.wait = data.rl.wait_time ?? rlStats.wait; }
  if (data.rr) { rrStats.throughput = data.rr.throughput ?? rrStats.throughput; rrStats.wait = data.rr.wait_time ?? rrStats.wait; }
  if (data.sjf) { sjfStats.throughput = data.sjf.throughput ?? sjfStats.throughput; sjfStats.wait = data.sjf.wait_time ?? sjfStats.wait; }
  if (data.fsfs) { fsfsStats.throughput = data.fsfs.throughput ?? fsfsStats.throughput; fsfsStats.wait = data.fsfs.wait_time ?? fsfsStats.wait; }
  if (data.priority) { priorityStats.throughput = data.priority.throughput ?? priorityStats.throughput; priorityStats.wait = data.priority.wait_time ?? priorityStats.wait; }
  renderComparison();
}
    /* Reward image */
    function loadRewardImage(src) {
      const img = document.getElementById('rewardImg');
      img.src = src; img.style.display = 'block';
      document.getElementById('rewardPlaceholder').style.display = 'none';
    }
    (function(){
      const t = new Image();
      t.onload = () => loadRewardImage('assets/training_curve.png');
      t.src = 'assets/training_curve.png';
    })();

    /* Stress test */
    async function triggerStressTest() {
      const btn = document.getElementById('stressBtn');
      btn.disabled = true; btn.classList.add('active'); btn.textContent = '⚡ RUNNING...';
      addLog('Stress test triggered → POST /api/stress-test', 'warn');
      try {
        const res = await fetch('http://localhost:5000/api/stress-test', {method:'POST'});
        addLog(res.ok ? 'Stress test started!' : 'Backend responded: '+res.status, res.ok?'success':'warn');
      } catch(e) {
        addLog('Backend offline — simulating spike locally', 'warn');
        demoCpu += 30; demoRam += 20; demoQueue += 15;
      }
      setTimeout(() => { btn.disabled=false; btn.classList.remove('active'); btn.textContent='⚡ STRESS TEST'; }, 8000);
    }

    /* Charts */
    function buildDataset(color) {
      return { label:'', data:[], borderColor:color, backgroundColor:color+'18', borderWidth:1.5, pointRadius:0, tension:0.4, fill:true };
    }
    function buildChart(id, color) {
      return new Chart(document.getElementById(id).getContext('2d'), {
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
      chart.data.labels.push(label);
      chart.data.datasets[0].data.push(value);
      if (chart.data.labels.length > MAX_POINTS) { chart.data.labels.shift(); chart.data.datasets[0].data.shift(); }
      chart.update();
    }

    /* Metrics */
    let prevCpu=null, prevRam=null, prevQueue=null;
    function updateMetrics(cpu, ram, queue) {
      document.getElementById('cpu-val').textContent = cpu.toFixed(1)+'%';
      document.getElementById('cpu-bar').style.width = cpu+'%';
      if (prevCpu!==null) { const d=(cpu-prevCpu).toFixed(1); document.getElementById('cpu-delta').textContent=(d>=0?'▲ +':'▼ ')+d+'% from last'; }
      prevCpu=cpu;

      document.getElementById('ram-val').textContent = ram.toFixed(1)+'%';
      document.getElementById('ram-bar').style.width = ram+'%';
      if (prevRam!==null) { const d=(ram-prevRam).toFixed(1); document.getElementById('ram-delta').textContent=(d>=0?'▲ +':'▼ ')+d+'% from last'; }
      prevRam=ram;

      document.getElementById('queue-val').textContent = queue;
      document.getElementById('queue-bar').style.width = Math.min((queue/50)*100,100)+'%';
      if (prevQueue!==null) { const d=queue-prevQueue; document.getElementById('queue-delta').textContent=(d>=0?'▲ +':'▼ ')+d+' tasks from last'; }
      prevQueue=queue;
    }

    /* Socket.IO */
    addLog('Attempting Socket.IO connection...','info');
    let socket;
    try {
      socket = io('http://localhost:5000', {transports:['websocket'], reconnectionAttempts:5});

      socket.on('connect', () => {
        document.getElementById('conn-status').textContent = 'CONNECTED · '+socket.id.slice(0,8);
        addLog('Connected — socket id: '+socket.id,'success');
      });
      socket.on('disconnect', r => { document.getElementById('conn-status').textContent='DISCONNECTED'; addLog('Disconnected: '+r,'warn'); });
      socket.on('connect_error', e => { document.getElementById('conn-status').textContent='BACKEND OFFLINE (DEMO MODE)'; addLog('Connection error: '+e.message,'warn'); });

      socket.on('metrics', d => {
        const label = d.timestamp || ts();
        pushPoint(cpuChart, label, d.cpu); pushPoint(ramChart, label, d.ram);
        updateMetrics(d.cpu, d.ram, d.queue);
        addLog(`metrics → cpu=${d.cpu.toFixed(1)}% ram=${d.ram.toFixed(1)}% q=${d.queue}`,'info');
      });

      socket.on('decision', d => addDecision(d.pid, d.action));
      socket.on('comparison', d => updateComparison(d));
      socket.on('reward_image', d => { loadRewardImage(d.path); addLog('Training curve loaded from P1','success'); });
      socket.onAny((ev,...a) => { if (!['metrics','decision','comparison','reward_image'].includes(ev)) addLog(`${ev} → ${JSON.stringify(a)}`,'info'); });

    } catch(e) { addLog('Socket.IO init failed: '+e.message,'warn'); }

    /* Demo mode */
    let demoCpu=30, demoRam=45, demoQueue=5, demoTick=0;
    const DEMO_PIDS    = [101,204,317,422,538,611,749,823];
    const DEMO_ACTIONS = ['Scheduled','Scheduled','Scheduled','Preempted','Waiting','Completed'];

    renderComparison();

    setInterval(() => {
      if (socket && socket.connected) return;
      demoTick++;
      demoCpu   = Math.max(5,  Math.min(95, demoCpu  + (Math.random()-0.48)*6));
      demoRam   = Math.max(20, Math.min(90, demoRam  + (Math.random()-0.48)*4));
      demoQueue = Math.max(0,  Math.min(50, demoQueue + Math.round((Math.random()-0.5)*3)));
      const label = ts();
      pushPoint(cpuChart, label, +demoCpu.toFixed(1));
      pushPoint(ramChart, label, +demoRam.toFixed(1));
      updateMetrics(demoCpu, demoRam, demoQueue);
      addDecision(DEMO_PIDS[Math.floor(Math.random()*DEMO_PIDS.length)], DEMO_ACTIONS[Math.floor(Math.random()*DEMO_ACTIONS.length)]);
      if (demoTick%3===0) {
        rlStats.throughput = Math.max(1, rlStats.throughput+(Math.random()-0.35)*0.4);
        rrStats.throughput = Math.max(1, rrStats.throughput+(Math.random()-0.5)*0.3);
        rlStats.wait = Math.max(5, rlStats.wait+(Math.random()-0.55)*2);
        rrStats.wait = Math.max(5, rrStats.wait+(Math.random()-0.45)*2);
        renderComparison();
      }
    }, 1500);