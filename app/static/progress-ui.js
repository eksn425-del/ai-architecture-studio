/* Execution summaries only: no hidden reasoning, tool arguments or credentials. */
(function () {
  const projects = new Map();
  function snapshot(history, projectId) {
    const changed = projectId && history.dataset.scrollProject !== projectId;
    if (projectId) history.dataset.scrollProject = projectId;
    return {top: changed ? 0 : history.scrollTop,
      follow: changed || history.scrollHeight - history.clientHeight - history.scrollTop < 90};
  }
  function restore(history, position) {
    history.scrollTop = position.follow ? history.scrollHeight : position.top;
  }
  function render(projectId, history) {
    if (!history || !projectId) return;
    const position = snapshot(history);
    for (const run of projects.get(projectId) || []) {
      let article = history.querySelector(`[data-activity-id="${run.id}"]`);
      if (!article) {
        article = document.createElement('article');
        article.className = 'chat-message assistant activity-message';
        article.dataset.activityId = run.id;
        const heading = document.createElement('header');
        heading.textContent = '建筑 Agent · 执行记录';
        article.append(heading, document.createElement('ol'));
        let user = history.querySelector(`[data-activity-anchor="${run.anchor || run.id}"]`) ||
          (!run.anchor && Array.from(history.querySelectorAll('.chat-message.user')).filter(item => {
            const created = Number(item.dataset.createdMs);
            return created > run.started * 1000 - 5000 && created < run.started * 1000 + 5000;
          }).at(-1));
        if (!user && !run.finished && history.querySelector('.pending-reply')) {
          const pendingUser = Array.from(history.querySelectorAll('.chat-message.user')).at(-1);
          if (pendingUser && !pendingUser.dataset.activityAnchor && !Number(pendingUser.dataset.createdMs)) {
            user = pendingUser;
            user.dataset.activityAnchor = run.anchor || run.id;
          }
        }
        if (user) user.after(article);
        else continue;
      }
      const list = article.querySelector('ol');
      const known = new Set(Array.from(list.children, item => item.dataset.eventId));
      for (const event of run.events || []) {
        if (known.has(event.id)) continue;
        const item = document.createElement('li');
        item.dataset.eventId = event.id;
        item.className = event.status === 'warning' ? 'activity-warning' : '';
        item.textContent = event.text;
        list.append(item);
      }
      article.dataset.running = String(!run.finished);
    }
    restore(history, position);
    const button = document.getElementById('latest-activity');
    if (button) button.hidden = history.scrollHeight - history.clientHeight - history.scrollTop < 90;
  }
  function bind(history, controls) {
    if (!history || !controls || document.getElementById('latest-activity')) return;
    const button = document.createElement('button');
    button.id = 'latest-activity';
    button.type = 'button';
    button.className = 'button-quiet';
    button.textContent = '回到最新进度 ↓';
    button.hidden = true;
    controls.append(button);
    button.addEventListener('click', () => { history.scrollTop = history.scrollHeight; button.hidden = true; });
    history.addEventListener('scroll', () => {
      button.hidden = !history.querySelector('.activity-message') || history.scrollHeight - history.clientHeight - history.scrollTop < 90;
    }, {passive: true});
  }
  window.KStudioActivity = {snapshot, restore, render, bind,
    remember(projectId, runs) { if (Array.isArray(runs)) projects.set(projectId, runs); }};
})();
