import { useEffect, useState } from 'react'
import IndexView from './components/IndexView.jsx'
import DetailView from './components/DetailView.jsx'

function useHashRoute() {
  const [hash, setHash] = useState(() => window.location.hash)
  useEffect(() => {
    const onChange = () => setHash(window.location.hash)
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  const m = hash.match(/^#\/anime\/([^/?#]+)/)
  return { key: m ? m[1] : null, hash }
}

export default function App() {
  const [db, setDb] = useState(null)
  const [state, setState] = useState('loading')
  const { key } = useHashRoute()

  const fallbackTitle = key && db?.titles ? db.titles.find((t) => t.key === key) : null
  const [detailedTitle, setDetailedTitle] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // 1. Initial catalog fetch (lightweight fast indexed data)
  useEffect(() => {
    fetch('/api/anime.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d) => {
        setDb(d)
        setState('ready')
      })
      .catch((e) => {
        console.error(e)
        setState(`error: ${e.message}`)
      })
  }, [])

  // 2. On-demand detail dossier fetch when opening #/anime/:key
  useEffect(() => {
    if (!key) {
      setDetailedTitle(null)
      setDetailLoading(false)
      return
    }

    let isMounted = true
    setDetailLoading(true)
    fetch(`/api/title/${key}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (isMounted) {
          if (data && !data.error) {
            setDetailedTitle(data)
          } else {
            setDetailedTitle(fallbackTitle)
          }
          setDetailLoading(false)
        }
      })
      .catch(() => {
        if (isMounted) {
          setDetailedTitle(fallbackTitle)
          setDetailLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [key, fallbackTitle])

  // --- Early conditional returns (placed strictly AFTER all hooks) ---
  if (state === 'loading') {
    return (
      <div className="state-msg">
        <p>· загрузка регистра ·</p>
      </div>
    )
  }

  if (state !== 'ready' || !db) {
    return (
      <div className="state-msg">
        <p className="err">не удалось загрузить /api/anime.json</p>
        <p style={{ marginTop: 8, color: '#6f6757' }}>
          запустите API: python backend/server.py
        </p>
      </div>
    )
  }

  const activeTitle = detailedTitle || fallbackTitle

  if (key && !detailLoading && !activeTitle) {
    return (
      <div className="state-msg">
        <p className="err">тайтл «{key}» не найден</p>
        <a href="#/">← к каталогу</a>
      </div>
    )
  }

  return (
    <div className="wrap">
      <Header db={db} />
      {key ? (
        detailLoading && !activeTitle ? (
          <div className="state-msg"><p>· загрузка досье тайтла ·</p></div>
        ) : (
          <DetailView title={activeTitle} />
        )
      ) : (
        <IndexView titles={db.titles} />
      )}
      <footer className="foot">
        <p>
          АНИМЕ РЕГИСТР · собрано {db.titles.length} тайтлов из проверенных открытых источников ·
          Единый агрегатор Animan · обновлено {db.generated_at_utc?.replace('T', ' ').slice(0, 16)} UTC
        </p>
        <p>
          Источники: AniList (GraphQL), Shikimori (REST API), AnimeThemes.moe (музыка и видео), Manga (MangaDex, AniList, Shikimori), Kodik (HLS плеер и озвучки)
        </p>
      </footer>
    </div>
  )
}

function Header({ db }) {
  return (
    <header className="masthead">
      <a href="#/" className="masthead__brand">
        <span className="masthead__mark">台</span>
        <div>
          <h1 className="masthead__title">АНИМЕ РЕГИСТР</h1>
          <span className="masthead__jp">アニメ台帳 · ANIMAN</span>
        </div>
      </a>
      <div className="masthead__meta">
        {db.titles.length} тайтлов · SQLite FTS5
        <br />
        агрегатор: <b>ANIMAN</b>
      </div>
    </header>
  )
}
