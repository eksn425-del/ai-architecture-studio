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
      // Aggregate the display; every original audit receipt remains available.
      const grouped = new Map();
      for (const event of run.events || []) {
        const key = event.group || event.text.replace(/，(?:已收到执行结果|正在处理返回的问题)$/, '');
        let group = grouped.get(key);
        if (!group) { group = {key, count:0, warnings:0}; grouped.set(key, group); }
        group.lastIndex = (run.events || []).indexOf(event);
        group.count++; group.warnings += event.status === 'warning' ? 1 : 0;
      }
      list.replaceChildren();
      for (const group of Array.from(grouped.values()).sort((a,b) => a.lastIndex-b.lastIndex).slice(-4)) {
        const item = document.createElement('li');
        item.className = group.warnings ? 'activity-warning' : '';
        item.textContent = group.key + (group.count > 1 ? ` · ${group.count} 条记录` : '')
          + (group.warnings ? ` · ${group.warnings} 次问题` : '');
        list.append(item);
      }
      let details = article.querySelector('details');
      if (!details) { details = document.createElement('details'); article.append(details); }
      const opened = details.open;
      details.replaceChildren();
      const summary = document.createElement('summary');
      summary.textContent = `查看本轮 ${(run.events || []).length} 条执行记录`;
      const raw = document.createElement('ol');
      for (const event of run.events || []) {
        const item = document.createElement('li'); item.textContent = event.text;
        item.className = event.status === 'warning' ? 'activity-warning' : ''; raw.append(item);
      }
      details.append(summary, raw); details.open = opened;
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
