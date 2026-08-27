import { useState, useMemo } from 'react'
import { SOURCES } from '../sources.js'

export default function IndexView({ titles }) {
  const [query, setQuery] = useState('')
  const [selectedGenre, setSelectedGenre] = useState('')
  const [selectedVoiceover, setSelectedVoiceover] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [minScore, setMinScore] = useState('')
  const [sortBy, setSortBy] = useState('score_desc')

  // Extract all unique genres from titles with counts
  const genreFacets = useMemo(() => {
    const counts = {}
    for (const t of titles) {
      const gList = t.sources?.animan?.facts?.genres || []
      for (const g of gList) {
        counts[g] = (counts[g] || 0) + 1
      }
    }
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
  }, [titles])

  // Extract all unique Kodik voiceover studios from titles with counts
  const voiceoverFacets = useMemo(() => {
    const counts = {}
    for (const t of titles) {
      const kodik = t.sources?.animan?.kodik || {}
      for (const sName of Object.keys(kodik)) {
        // Strip season suffixes like " (Сезон 2)" for clean studio aggregation
        const baseName = sName.replace(/\s*\(Сезон\s*\d+\)/i, '').trim()
        counts[baseName] = (counts[baseName] || 0) + 1
      }
    }
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
  }, [titles])

  // Extract available formats and statuses
  const formatFacets = useMemo(() => {
    const set = new Set()
    for (const t of titles) {
      const fmt = t.sources?.animan?.facts?.format_ru
      if (fmt) set.add(fmt)
    }
    return Array.from(set)
  }, [titles])

  const statusFacets = useMemo(() => {
    const set = new Set()
    for (const t of titles) {
      const st = t.sources?.animan?.facts?.status_ru
      if (st) set.add(st)
    }
    return Array.from(set)
  }, [titles])

  // Multi-facet filtering and sorting
  const filteredTitles = useMemo(() => {
    return titles
      .filter((t) => {
        const an = t.sources?.animan
        const facts = an?.facts || {}
        const mainTitles = an?.titles?.main || {}
        const scores = an?.scores || {}

        // 1. Text Search (Russian, English, Japanese, Synonyms, Key)
        if (query.trim()) {
          const q = query.toLowerCase().trim()
          const ru = (mainTitles.ru || '').toLowerCase()
          const en = (mainTitles.en || t.names?.en || '').toLowerCase()
          const ja = (mainTitles.ja || t.names?.jp || '').toLowerCase()
          const desc = (an?.description?.ru || '').toLowerCase()
          const matchTitle = ru.includes(q) || en.includes(q) || ja.includes(q) || desc.includes(q) || t.key.includes(q)
          if (!matchTitle) return false
        }

        // 2. Genre Filter
        if (selectedGenre) {
          const genres = facts.genres || []
          if (!genres.includes(selectedGenre)) return false
        }

        // 3. Kodik Voiceover Studio Filter
        if (selectedVoiceover) {
          const kodikStudios = Object.keys(an?.kodik || {})
          const hasStudio = kodikStudios.some((s) => s.toLowerCase().includes(selectedVoiceover.toLowerCase()))
          if (!hasStudio) return false
        }

        // 4. Format Filter
        if (selectedFormat) {
          if (facts.format_ru !== selectedFormat) return false
        }

        // 5. Status Filter
        if (selectedStatus) {
          if (facts.status_ru !== selectedStatus) return false
        }

        // 6. Minimum Score Filter
        if (minScore) {
          const minNum = parseFloat(minScore)
          if (scores.average == null || scores.average < minNum) return false
        }

        return true
      })
      .sort((a, b) => {
        const anA = a.sources?.animan || {}
        const anB = b.sources?.animan || {}
        const scoreA = anA.scores?.average ?? 0
        const scoreB = anB.scores?.average ?? 0
        const yearA = parseInt(anA.facts?.year || '0', 10)
        const yearB = parseInt(anB.facts?.year || '0', 10)
        const titleA = anA.titles?.main?.ru || a.names?.en || ''
        const titleB = anB.titles?.main?.ru || b.names?.en || ''
        const epsA = anA.facts?.episodes_total ?? 0
        const epsB = anB.facts?.episodes_total ?? 0

        switch (sortBy) {
          case 'score_desc':
            return scoreB - scoreA || yearB - yearA
          case 'year_desc':
            return yearB - yearA || scoreB - scoreA
          case 'year_asc':
            return yearA - yearB || scoreB - scoreA
          case 'title_asc':
            return titleA.localeCompare(titleB, 'ru')
          case 'episodes_desc':
            return epsB - epsA
          default:
            return scoreB - scoreA
        }
      })
  }, [titles, query, selectedGenre, selectedVoiceover, selectedFormat, selectedStatus, minScore, sortBy])

  const hasActiveFilters = Boolean(
    query || selectedGenre || selectedVoiceover || selectedFormat || selectedStatus || minScore || sortBy !== 'score_desc'
  )

  const handleResetFilters = () => {
    setQuery('')
    setSelectedGenre('')
    setSelectedVoiceover('')
    setSelectedFormat('')
    setSelectedStatus('')
    setMinScore('')
    setSortBy('score_desc')
  }

  return (
    <div>
      <div className="catalog-hero">
        <p className="lede">
          Единый регистр аниме на базе <b>SQLite с индексацией и FTS5-поиском</b>, собранный из проверенных источников (<b>AniList</b>, <b>Shikimori</b>, <b>AnimeThemes</b>, <b>MangaDex</b>, <b>Kodik</b>).
        </p>

        {/* Global Search Bar */}
        <div className="search-bar-wrap">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="Поиск по названию (рус/en/jp), описанию или ключу..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query ? (
            <button className="search-clear" onClick={() => setQuery('')}>✕</button>
          ) : null}
        </div>

        {/* Rich Multi-Facet Filters Panel */}
        <div className="catalog-filters-panel">
          {/* Quick Genre Chips */}
          <div className="genre-chips-wrap">
            <div className="filter-label">🏷️ Жанры аниме:</div>
            <div className="genre-chips-row">
              <button
                type="button"
                className={`btn-genre-chip ${!selectedGenre ? 'active' : ''}`}
                onClick={() => setSelectedGenre('')}
              >
                Все жанры ({titles.length})
              </button>
              {genreFacets.map((g) => (
                <button
                  key={g.name}
                  type="button"
                  className={`btn-genre-chip ${selectedGenre === g.name ? 'active' : ''}`}
                  onClick={() => setSelectedGenre(selectedGenre === g.name ? '' : g.name)}
                >
                  {g.name} ({g.count})
                </button>
              ))}
            </div>
          </div>

          {/* Selectors Grid: Voiceover, Format, Status, Score, Sort */}
          <div className="filters-grid-row">
            {/* Kodik Voiceover Studio */}
            <div className="filter-group">
              <label className="filter-label">🎙️ Озвучка / Студия</label>
              <select
                className="filter-select"
                value={selectedVoiceover}
                onChange={(e) => setSelectedVoiceover(e.target.value)}
              >
                <option value="">Все озвучки</option>
                {voiceoverFacets.map((vo) => (
                  <option key={vo.name} value={vo.name}>
                    {vo.name} ({vo.count})
                  </option>
                ))}
              </select>
            </div>

            {/* Format */}
            <div className="filter-group">
              <label className="filter-label">📺 Формат</label>
              <select
                className="filter-select"
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
              >
                <option value="">Все форматы</option>
                {formatFacets.map((fmt) => (
                  <option key={fmt} value={fmt}>{fmt}</option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div className="filter-group">
              <label className="filter-label">⏱️ Статус</label>
              <select
                className="filter-select"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
              >
                <option value="">Все статусы</option>
                {statusFacets.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            {/* Rating */}
            <div className="filter-group">
              <label className="filter-label">⭐ Рейтинг</label>
              <select
                className="filter-select"
                value={minScore}
                onChange={(e) => setMinScore(e.target.value)}
              >
                <option value="">Любой рейтинг</option>
                <option value="8.5">★ 8.5 и выше</option>
                <option value="8.0">★ 8.0 и выше</option>
                <option value="7.5">★ 7.5 и выше</option>
              </select>
            </div>

            {/* Sorting */}
            <div className="filter-group">
              <label className="filter-label">🎚️ Сортировка</label>
              <select
                className="filter-select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="score_desc">★ По рейтингу</option>
                <option value="year_desc">📅 Сначала новые</option>
                <option value="year_asc">📅 Сначала старые</option>
                <option value="title_asc">🔤 По названию (А–Я)</option>
                <option value="episodes_desc">📑 По кол-ву серий</option>
              </select>
            </div>
          </div>

          {/* Active Summary & Reset */}
          <div className="filter-active-summary">
            <div>
              Найдено: <span className="filter-count-badge">{filteredTitles.length}</span> из {titles.length} тайтлов
            </div>
            {hasActiveFilters ? (
              <button type="button" className="btn-reset-filters" onClick={handleResetFilters}>
                ✕ Сбросить все фильтры
              </button>
            ) : null}
          </div>
        </div>
      </div>

      {/* Grid of Anime Cards */}
      <div className="grid">
        {filteredTitles.map((t, i) => (
          <Card key={t.key} title={t} index={i} />
        ))}
      </div>

      {/* Empty State */}
      {filteredTitles.length === 0 ? (
        <div className="empty-search">
          <p>Ничего не найдено по выбранным фильтрам</p>
          <button type="button" className="btn-reset-filters" style={{ marginTop: '10px' }} onClick={handleResetFilters}>
            Сбросить фильтры
          </button>
        </div>
      ) : null}
    </div>
  )
}

function Card({ title, index }) {
  const key = title.key
  const an = title.sources?.animan
  const mainTitles = an?.titles?.main || {}
  const ruTitle = mainTitles.ru || title.names?.en
  const enTitle = mainTitles.en
  const jaTitle = mainTitles.ja

  const poster = an?.posters?.[0]?.url || title.sources?.anilist?.coverImage?.large || null
  const facts = an?.facts || {}
  const scores = an?.scores || {}
  const avg = scores.average

  const metaPills = [
    facts.format_ru,
    facts.episodes_total != null ? `${facts.episodes_total} эп.` : null,
    facts.year,
    facts.status_ru,
  ].filter(Boolean)

  const errCount = Object.keys(title.errors || {}).length
  const kodikStudiosCount = Object.keys(an?.kodik || {}).length

  return (
    <a
      className="card"
      href={`#/anime/${key}`}
    >
      <div className="card__cover">
        {poster ? (
          <img src={poster} alt={ruTitle} loading="lazy" referrerPolicy="no-referrer" />
        ) : (
          <div className="card__placeholder">🎬</div>
        )}
        {avg ? (
          <div className="card__rating-badge">
            ★ {avg}
          </div>
        ) : null}
      </div>
      <div className="card__body">
        <div className="card__num">№ {String(index + 1).padStart(2, '0')}</div>
        <div className="card__title">{ruTitle}</div>
        {enTitle && enTitle !== ruTitle ? <div className="card__en">{enTitle}</div> : null}
        {jaTitle ? <div className="card__jp">{jaTitle}</div> : null}

        <div className="card__meta">
          {metaPills.join(' · ') || '—'}
        </div>

        {facts.genres?.length ? (
          <div className="card__genres">
            {facts.genres.slice(0, 3).map((g) => (
              <span key={g} className="card__genre-tag">{g}</span>
            ))}
          </div>
        ) : null}

        <div className="card__srcs" title={errCount ? `Ошибок сбора: ${errCount}` : 'Все 4 источника собраны'}>
          {SOURCES.map((s) => (
            <span
              key={s.key}
              className={`dot ${title.sources?.[s.key] ? 'on' : ''} ${title.errors?.[s.key] ? 'warn' : ''}`}
              title={`${s.name}: ${title.sources?.[s.key] ? 'собран' : 'нет данных'}`}
            />
          ))}
          {kodikStudiosCount > 0 ? (
            <span className="srcs-count-label" style={{ color: '#3498db' }}>
              🎙️ {kodikStudiosCount} озвучек
            </span>
          ) : (
            <span className="srcs-count-label">4 источника</span>
          )}
        </div>
      </div>
    </a>
  )
}
