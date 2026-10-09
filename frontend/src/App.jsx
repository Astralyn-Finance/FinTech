import './App.css'

const agents = [
  {
    name: 'News Agent',
    subtitle: 'News collection & processing',
    color: '#3B82F6',
    tasks: [
      { title: 'Collect market news', id: 'TASK-001', status: 'Running', detail: 'Fetching financial news sources' },
      { title: 'Clean news articles', id: 'TASK-002', status: 'Queued', detail: 'Waiting for collection to finish' },
    ],
  },
  {
    name: 'Quant Agent',
    subtitle: 'Market data & technical analysis',
    color: '#8B5CF6',
    tasks: [
      { title: 'Calculate moving averages', id: 'TASK-003', status: 'Running', detail: 'Processing price data' },
    ],
  },
  {
    name: 'Sentiment Agent',
    subtitle: 'Market sentiment analysis',
    color: '#F59E0B',
    tasks: [
      { title: 'Analyze market sentiment', id: 'TASK-004', status: 'Queued', detail: 'Awaiting news data' },
    ],
  },
  {
    name: 'Portfolio Optimizer',
    subtitle: 'Portfolio allocation',
    color: '#10B981',
    tasks: [
      { title: 'Optimize asset weights', id: 'TASK-005', status: 'Completed', detail: 'Demo task finished' },
    ],
  },
  {
    name: 'Risk & Validation',
    subtitle: 'Risk checks & validation',
    color: '#EF4444',
    tasks: [
      { title: 'Validate portfolio risk', id: 'TASK-006', status: 'Blocked', detail: 'Waiting for optimized weights' },
    ],
  },
  {
    name: 'Report Agent',
    subtitle: 'Final report generation',
    color: '#06B6D4',
    tasks: [
      { title: 'Prepare portfolio report', id: 'TASK-007', status: 'Queued', detail: 'Waiting for risk validation' },
    ],
  },
]

function App() {
  const allTasks = agents.flatMap((agent) => agent.tasks)
  const running = allTasks.filter((task) => task.status === 'Running').length
  const completed = allTasks.filter((task) => task.status === 'Completed').length
  const queued = allTasks.filter((task) => task.status === 'Queued').length

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">F</div>
          <div>
            <h2>FinPilot</h2>
            <span>INTELLIGENT FINANCE</span>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>
        <div className="nav-item active"><span>▦</span> Agent Overview</div>
        <div className="nav-item"><span>◷</span> Execution History</div>
        <div className="nav-item"><span>◈</span> Portfolio Analytics</div>

        <div className="sidebar-bottom">
          <div className="user-avatar">GB</div>
          <div className="user-info">
            <strong>My Workspace</strong>
            <span>FinTech Developer</span>
          </div>
          <span className="settings-icon">⚙</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">Workspace <span>/</span> Agent Overview</div>
          <div className="topbar-right">
            <span className="demo-badge"><span /> DEMO DATA</span>
            <div className="top-avatar">GB</div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <p className="eyebrow">ORCHESTRATION CENTER</p>
            <h1>Agent Command Center</h1>
            <p className="page-description">
              Monitor your financial intelligence pipeline and agent activity.
            </p>
          </div>
          <button className="refresh-button" onClick={() => window.location.reload()}>
            ↻ Refresh view
          </button>
        </section>

        <section className="stats-grid">
          <div className="stat-card">
            <div className="stat-top"><span>Total Tasks</span><span className="stat-icon blue">▤</span></div>
            <div className="stat-number">{allTasks.length}</div>
            <div className="stat-caption">Across all agent stages</div>
          </div>
          <div className="stat-card">
            <div className="stat-top"><span>Running</span><span className="stat-icon purple">◉</span></div>
            <div className="stat-number">{running}</div>
            <div className="stat-caption"><span className="live-dot" /> Currently in progress</div>
          </div>
          <div className="stat-card">
            <div className="stat-top"><span>Completed</span><span className="stat-icon green">✓</span></div>
            <div className="stat-number">{completed}</div>
            <div className="stat-caption">Tasks finished in this demo</div>
          </div>
          <div className="stat-card">
            <div className="stat-top"><span>Queued</span><span className="stat-icon orange">◷</span></div>
            <div className="stat-number">{queued}</div>
            <div className="stat-caption">Waiting to be processed</div>
          </div>
        </section>

        <section className="board-heading">
          <div>
            <h2>Agent Workflow</h2>
            <p>Track tasks as they move through the pipeline.</p>
          </div>
          <span className="task-count">{allTasks.length} tasks</span>
        </section>

        <section className="kanban-board">
          {agents.map((agent) => (
            <div className="kanban-column" key={agent.name}>
              <div className="column-heading">
                <span className="agent-dot" style={{ backgroundColor: agent.color }} />
                <h3>{agent.name}</h3>
                <span className="column-count">{agent.tasks.length}</span>
              </div>
              <p className="column-subtitle">{agent.subtitle}</p>

              <div className="task-list">
                {agent.tasks.map((task) => (
                  <article className="task-card" key={task.id}>
                    <div className="task-card-top">
                      <span className="task-id">{task.id}</span>
                      <button className="more-button" aria-label={`More options for ${task.title}`}>···</button>
                    </div>
                    <h4>{task.title}</h4>
                    <p className="task-detail">{task.detail}</p>
                    <div className="task-card-bottom">
                      <span className={`status status-${task.status.toLowerCase()}`}>
                        <span className="status-dot" />{task.status}
                      </span>
                      <span className="task-owner">{agent.name.split(' ')[0].slice(0, 2).toUpperCase()}</span>
                    </div>
                  </article>
                ))}
                <button className="add-task" disabled title="Task creation will be added after backend integration">
                  + Add task
                </button>
              </div>
            </div>
          ))}
        </section>

        <footer className="dashboard-footer">
          <span><span className="footer-dot" /> Dashboard UI preview</span>
          <span>Sample tasks only · Not connected to the backend yet</span>
        </footer>
      </main>
    </div>
  )
}

export default App