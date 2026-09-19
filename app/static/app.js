(() => {
  const projectId = document.body.dataset.projectId;
  const activity = document.querySelector('#activity');
  const chat = document.querySelector('#chat');
  const message = document.querySelector('#message');
  const status = document.querySelector('#status');
  const sendButton = chat?.querySelector('button');

  const statusClass = value => `status status-${String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
  const renderStatus = value => {
    if (!status) return;
    status.textContent = value;
    status.className = statusClass(value);
  };
  const addEvent = event => {
    if (!activity) return;
    activity.querySelector('.empty')?.remove();
    const item = document.createElement('article');
    item.className = 'event';
    item.innerHTML = `<span class="event-dot"></span><div><div class="event-meta"><span class="event-agent"></span><span class="event-kind"></span></div><p class="event-message"></p></div>`;
    item.querySelector('.event-agent').textContent = event.agent || 'System';
    item.querySelector('.event-kind').textContent = event.kind || 'update';
    item.querySelector('.event-message').textContent = event.message || '';
    activity.appendChild(item);
    activity.scrollTop = activity.scrollHeight;
  };

  if (chat) {
    chat.addEventListener('submit', async event => {
      event.preventDefault();
      const text = message.value.trim();
      if (!text) return;
      sendButton.disabled = true;
      sendButton.textContent = 'Starting...';
      try {
        const response = await fetch(`/projects/${projectId}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text }) });
        if (!response.ok) throw new Error('The run could not be started.');
        addEvent({ agent: 'You', kind: 'requirement', message: text });
        message.value = '';
        renderStatus('running');
      } catch (error) {
        addEvent({ agent: 'System', kind: 'error', message: error.message });
      } finally {
        sendButton.disabled = false;
        sendButton.textContent = 'Send request';
      }
    });
  }

  if (projectId) {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${location.host}/ws/projects/${projectId}`);
    socket.addEventListener('message', event => addEvent(JSON.parse(event.data)));
    socket.addEventListener('open', () => renderStatus('connected'));
    window.setInterval(async () => {
      const response = await fetch(`/projects/${projectId}/api/state`);
      if (response.ok) renderStatus((await response.json()).status);
    }, 5000);
  }
})();
