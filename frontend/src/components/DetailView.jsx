import AnimanPanel from './AnimanPanel.jsx'

export default function DetailView({ title }) {
  const animan = title.sources?.animan
  const errors = Object.entries(title.errors || {})

  if (!animan) {
    return (
      <div>
        <a className="back" href="#/">
          ← КАТАЛОГ
        </a>
        <div className="panel" style={{ color: '#6f6757', marginTop: 20 }}>
          Данные Animan ещё не сформированы для этого тайтла.
        </div>
      </div>
    )
  }

  return (
    <div className="detail-view">
      <div className="detail-nav">
        <a className="back" href="#/">
          ← К КАТАЛОГУ
        </a>
        <div className="detail-crumbs">
          <span className="crumb-key">{title.key}</span>
          <span className="crumb-sep">·</span>
          <span className="crumb-name">{animan.titles?.main?.ru || title.names.en}</span>
        </div>
      </div>

      {errors.length > 0 ? (
        <div className="panel" style={{ borderColor: 'rgba(229,72,46,.5)', marginBottom: 20 }}>
          <div className="sec__label" style={{ color: 'var(--accent)' }}>Замечания сбора данных</div>
          {errors.map(([k, e]) => (
            <div key={k} className="sec__body" style={{ fontSize: 13 }}>
              <b>{k}</b>: {e.message || e.type} <span style={{ color: '#6f6757' }}>({e.type})</span>
            </div>
          ))}
        </div>
      ) : null}

      <AnimanPanel panel={animan} title={title} titleKey={title.key} mangaMap={title.manga_map} />
    </div>
  )
}
