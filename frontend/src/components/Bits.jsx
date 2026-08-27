/* Shared small renderers used by source panels */

export function Section({ label, children }) {
  return (
    <div className="sec">
      <div className="sec__label">{label}</div>
      <div className="sec__body">{children}</div>
    </div>
  )
}

export function Facts({ items }) {
  const rows = items.filter(([, v]) => v != null && v !== '' && !(Array.isArray(v) && !v.length))
  if (!rows.length) return null
  return (
    <div className="facts">
      {rows.map(([k, v]) => (
        <div className="f" key={k}>
          <span className="k">{k}</span>
          <span className="v">{renderValue(v)}</span>
        </div>
      ))}
    </div>
  )
}

export function renderValue(v) {
  if (Array.isArray(v)) return <Chips items={v} />
  if (typeof v === 'boolean') return v ? 'да' : 'нет'
  if (typeof v === 'object' && v !== null) {
    return (
      <ul className="rows">
        {Object.entries(v).map(([k, val]) => (
          <li key={k}>
            <b>{k}</b>: {String(val)}
          </li>
        ))}
      </ul>
    )
  }
  return String(v)
}

export function Chips({ items, hi }) {
  if (!items || !items.length) return null
  return (
    <div className="chips">
      {items.map((x, i) => (
        <span key={`${x}-${i}`} className={`chip ${hi ? 'hi' : ''}`}>
          {x}
        </span>
      ))}
    </div>
  )
}

export function List({ items, max }) {
  if (!items || !items.length) return <span style={{ color: '#6f6757' }}>—</span>
  const shown = max && items.length > max ? items.slice(0, max) : items
  const extra = max && items.length > max ? items.length - max : 0
  return (
    <ul className="rows">
      {shown.map((x, i) => (
        <li key={i}>{String(x)}</li>
      ))}
      {extra ? <li style={{ color: '#6f6757' }}>… ещё {extra}</li> : null}
    </ul>
  )
}

export function MiniTable({ headers, rows }) {
  if (!rows || !rows.length) return null
  return (
    <div className="mini-scroll">
      <table className="mini">
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) => (
                <td key={j}>{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Imgs({ urls }) {
  if (!urls || !urls.length) return null
  return (
    <div className="imgs">
      {urls.map((u, i) => (
        <img key={i} src={u} alt="" loading="lazy" referrerPolicy="no-referrer" />
      ))}
    </div>
  )
}

export function Html({ html }) {
  if (!html) return null
  const safe = html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<iframe[\s\S]*?<\/iframe>/gi, '')
  return (
    <div
      style={{ lineHeight: 1.7 }}
      dangerouslySetInnerHTML={{ __html: safe }}
    />
  )
}

export function JsonBlock({ data }) {
  if (data == null) return null
  return (
    <details className="json-block">
      <summary>СЫРЫЕ ДАННЫЕ · JSON (всё, что вернул источник)</summary>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </details>
  )
}

/* ------------------------------------------------------------------ */
/* Everything: auto-visualize any payload field a panel did not render */
/* ------------------------------------------------------------------ */

const META_KEYS = ['source', 'fetched_at_utc', 'duration_s', '_query_fields']

function isImgUrl(s) {
  return /^https?:\/\/[^\s]+\.(jpe?g|png|webp|gif|avif|bmp)(\?[^\s]*)?$/i.test(s)
}

function UrlNode({ s }) {
  if (isImgUrl(s)) {
    return (
      <span className="e-urlimg">
        <img src={s} alt="" loading="lazy" referrerPolicy="no-referrer" />
        <a href={s} target="_blank" rel="noreferrer">
          {s.length > 96 ? `${s.slice(0, 96)}…` : s}
        </a>
      </span>
    )
  }
  return (
    <a href={s} target="_blank" rel="noreferrer">
      {s}
    </a>
  )
}

function cellNode(v) {
  if (v == null) return '—'
  if (Array.isArray(v)) {
    const s = v
      .map((x) => (x && typeof x === 'object' ? JSON.stringify(x) : String(x)))
      .join('; ')
    return <span className="e-plain">{s.length > 180 ? `${s.slice(0, 180)}…` : s}</span>
  }
  if (typeof v === 'object') {
    const s = JSON.stringify(v)
    return <span className="e-plain">{s.length > 180 ? `${s.slice(0, 180)}…` : s}</span>
  }
  if (typeof v === 'boolean') return v ? 'да' : 'нет'
  const s = String(v)
  if (/^https?:\/\//i.test(s)) return <UrlNode s={s} />
  return s
}

function ArrTable({ items }) {
  const keys = Object.keys(items[0] || {}).slice(0, 7)
  const shown = items.slice(0, 40)
  const more = items.length - shown.length
  return (
    <div className="mini-scroll">
      <table className="mini">
        <thead>
          <tr>
            {keys.map((k) => (
              <th key={k}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((o, i) => (
            <tr key={i}>
              {keys.map((k) => (
                <td key={k}>{cellNode(o[k])}</td>
              ))}
            </tr>
          ))}
        </tbody>
        {more > 0 ? (
          <tfoot>
            <tr>
              <td colSpan={keys.length} className="muted">
                … ещё {more} записей
              </td>
            </tr>
          </tfoot>
        ) : null}
      </table>
    </div>
  )
}

function valueNode(v, depth) {
  if (v == null) return <span className="muted">—</span>
  if (typeof v === 'boolean') return v ? 'да' : 'нет'
  if (Array.isArray(v)) {
    const prims = v.filter((x) => x == null || ['string', 'number', 'boolean'].includes(typeof x))
    if (prims.length === v.length) {
      if (!v.length) return <span className="muted">—</span>
      const shown = v.slice(0, 60).map(String)
      return (
        <>
          <Chips items={shown} />
          {v.length > 60 ? <span className="muted"> … ещё {v.length - 60}</span> : null}
        </>
      )
    }
    const objs = v.filter((x) => x && typeof x === 'object')
    if (objs.length) return <ArrTable items={objs} />
    return <span className="e-plain">{JSON.stringify(v)}</span>
  }
  if (typeof v === 'object') {
    if (depth >= 4) {
      return <pre className="e-pre">{JSON.stringify(v, null, 2)}</pre>
    }
    return <Everything data={v} depth={depth + 1} />
  }
  const s = String(v)
  if (/^https?:\/\//i.test(s)) return <UrlNode s={s} />
  if (s.length > 500) {
    return (
      <details className="long">
        <summary>показать текст · {s.length} симв.</summary>
        <div className="e-text">{s}</div>
      </details>
    )
  }
  return <span className="e-plain">{s}</span>
}

export function Everything({ data, skip = [], depth = 0 }) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null
  const entries = Object.entries(data).filter(
    ([k, v]) => !META_KEYS.includes(k) && !skip.includes(k) && v != null,
  )
  if (!entries.length) return null
  const body = (
    <div className="facts">
      {entries.map(([k, v]) => (
        <div className="f" key={k}>
          <span className="k">{k}</span>
          <span className="v">{valueNode(v, depth)}</span>
        </div>
      ))}
    </div>
  )
  if (entries.length > 24) {
    return (
      <details className="ev">
        <summary>все прочие поля · {entries.length} шт · показать</summary>
        <div style={{ marginTop: 10 }}>{body}</div>
      </details>
    )
  }
  return body
}
