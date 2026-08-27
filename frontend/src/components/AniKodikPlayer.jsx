import React, { useState, useEffect, useRef, useMemo } from 'react'
import Hls from 'hls.js'

function formatSec(seconds) {
  if (seconds == null || isNaN(seconds) || seconds < 0) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function AniKodikPlayer({ animan, title, titleKey }) {
  // Kodik catalog from animan or fetched on-demand
  const kodikCatalog = animan?.kodik || {}
  const studios = useMemo(() => Object.keys(kodikCatalog), [kodikCatalog])
  const currentKey = titleKey || title?.key || animan?.key || animan?.facts?.key || ''
  const shikiId = title?.shikimori_id || animan?.facts?.shikimori_id || ''
  const malId = title?.sources?.anilist?.idMal || ''

  // Fallback / Rich episode metadata from Shikimori / AniList / Fillers DB
  const metaEpisodes = title?.episodes?.items || animan?.episodes?.items
  const metaEpMap = useMemo(() => {
    const map = new Map()
    for (const ep of metaEpisodes || []) {
      map.set(Number(ep.number), ep)
    }
    return map
  }, [metaEpisodes])

  // Active studio / fandub
  const [activeStudio, setActiveStudio] = useState(studios[0] || '')
  // Active episode number (1-indexed)
  const [activeEpNum, setActiveEpNum] = useState(1)
  // Active quality ('1080', '720', '480', '360')
  const [activeQuality, setActiveQuality] = useState('720')

  // Player Mode: 'hls' (Direct stream) vs 'iframe' (Kodik embed)
  const [playerMode, setPlayerMode] = useState('hls')
  const [theaterMode, setTheaterMode] = useState(false)
  const [viewMode, setViewMode] = useState('grid') // 'grid' | 'list'
  const [filterType, setFilterType] = useState('all') // 'all' | 'canon' | 'filler'
  const [epSearch, setEpSearch] = useState('')
  const [autoNext, setAutoNext] = useState(true)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)

  // Stream Resolution State
  const [resolving, setResolving] = useState(false)
  const [streamData, setStreamData] = useState(null)

  // Live video playback state
  const [currentTime, setCurrentTime] = useState(0)
  const [videoDuration, setVideoDuration] = useState(0)
  const [_isPlaying, setIsPlaying] = useState(false)

  // Floating Skip Indicators
  const [showOpSkip, setShowOpSkip] = useState(false)
  const [showEdSkip, setShowEdSkip] = useState(false)

  const videoRef = useRef(null)
  const hlsRef = useRef(null)
  const seekbarRef = useRef(null)

  // Sync active studio if studios change
  useEffect(() => {
    if (studios.length > 0 && (!activeStudio || !kodikCatalog[activeStudio])) {
      setActiveStudio(studios[0])
    }
  }, [studios, activeStudio, kodikCatalog])

  // Current studio episodes
  const currentStudioData = kodikCatalog[activeStudio]
  const currentEpisodesDict = useMemo(() => currentStudioData?.episodes || {}, [currentStudioData])
  const availableEpNumbers = useMemo(() => {
    return Object.keys(currentEpisodesDict)
      .map(Number)
      .filter((n) => Number.isFinite(n) && n > 0)
      .sort((a, b) => a - b)
  }, [currentEpisodesDict])

  // Current episode object from Kodik
  const currentEpEntry = currentEpisodesDict[String(activeEpNum)] || currentEpisodesDict[String(availableEpNumbers[0])] || null
  const currentMetaEp = metaEpMap.get(activeEpNum)

  // If activeEpNum is out of range for current studio, snap to first available
  useEffect(() => {
    if (availableEpNumbers.length > 0 && !availableEpNumbers.includes(activeEpNum)) {
      setActiveEpNum(availableEpNumbers[0])
    }
  }, [availableEpNumbers, activeEpNum])

  // On-Demand Stream Resolution when active episode or studio link changes
  useEffect(() => {
    if (!currentEpEntry?.link) {
      setStreamData(null)
      return
    }

    let isMounted = true
    const epLink = currentEpEntry.link

    async function resolveCurrentEpisode() {
      setResolving(true)
      try {
        const url = `/api/resolve?link=${encodeURIComponent(epLink)}&key=${encodeURIComponent(currentKey)}&ep=${activeEpNum}&mal_id=${encodeURIComponent(malId || shikiId)}`
        const resp = await fetch(url)
        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}`)
        }
        const data = await resp.json()
        if (isMounted) {
          if (data && data.links && Object.keys(data.links).length > 0) {
            setStreamData(data)
            // Pick highest available quality or keep current
            const availableQ = Object.keys(data.links)
            setActiveQuality((prevQ) => {
              if (availableQ.includes(prevQ)) return prevQ
              if (availableQ.includes('1080')) return '1080'
              if (availableQ.includes('720')) return '720'
              if (availableQ.includes('480')) return '480'
              return availableQ[0]
            })
          } else {
            throw new Error('Видеопоток не найден')
          }
        }
      } catch (err) {
        if (isMounted) {
          console.warn('Stream resolution failed, fallback to iframe:', err)
          // Fallback to iframe if direct HLS fails
          setPlayerMode('iframe')
        }
      } finally {
        if (isMounted) setResolving(false)
      }
    }

    resolveCurrentEpisode()

    return () => {
      isMounted = false
    }
  }, [currentEpEntry?.link, currentKey, activeEpNum])

  // Determine current active direct video URL
  const currentDirectUrl = useMemo(() => {
    if (!streamData?.links) return null
    const qObj = streamData.links[activeQuality] || streamData.links['720'] || streamData.links['480'] || Object.values(streamData.links)[0]
    return qObj?.Src || null
  }, [streamData, activeQuality])

  // Setup HLS.js Video Player
  useEffect(() => {
    const video = videoRef.current
    if (!video || !currentDirectUrl || playerMode !== 'hls') return

    if (hlsRef.current) {
      hlsRef.current.destroy()
      hlsRef.current = null
    }

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
        backBufferLength: 90,
      })
      hlsRef.current = hls

      hls.loadSource(currentDirectUrl)
      hls.attachMedia(video)

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.playbackRate = playbackSpeed
        video.play().catch(() => {
          // Autoplay policy: ignore error if user has not interacted
        })
      })

      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.warn('HLS Network error, attempting recovery...')
              hls.startLoad()
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.warn('HLS Media error, attempting recovery...')
              hls.recoverMediaError()
              break
            default:
              console.warn('HLS Fatal error, switching to iframe fallback:', data)
              hls.destroy()
              setPlayerMode('iframe')
              break
          }
        }
      })
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native Safari HLS
      video.src = currentDirectUrl
      video.playbackRate = playbackSpeed
      video.play().catch(() => {})
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy()
        hlsRef.current = null
      }
    }
  }, [currentDirectUrl, playerMode])

  // Skip Timestamps: Strictly authentic verified timestamps from Kodik / AniSkip
  const opSkip = useMemo(() => {
    // 1. Check Kodik / Backend resolved skips
    if (streamData?.skips?.length) {
      const s = streamData.skips.find((x) => x.type === 'op') || streamData.skips[0]
      if (s && s.start != null && s.end != null && s.end > s.start) {
        return { start_s: s.start, end_s: s.end, start_fmt: formatSec(s.start), end_fmt: formatSec(s.end) }
      }
    }
    // 2. Check metadata verified timestamps
    const ts = currentMetaEp?.timestamps?.op
    if (ts?.start_s != null && ts?.end_s != null && ts.end_s > ts.start_s) {
      return { start_s: ts.start_s, end_s: ts.end_s, start_fmt: ts.start_fmt || formatSec(ts.start_s), end_fmt: ts.end_fmt || formatSec(ts.end_s) }
    }
    return null
  }, [streamData, currentMetaEp])

  const edSkip = useMemo(() => {
    // 1. Check Kodik / Backend resolved skips
    if (streamData?.skips?.length > 1) {
      const s = streamData.skips.find((x) => x.type === 'ed') || streamData.skips[1]
      if (s && s.start != null && s.end != null && s.end > s.start) {
        return { start_s: s.start, end_s: s.end, start_fmt: formatSec(s.start), end_fmt: formatSec(s.end) }
      }
    }
    // 2. Check metadata verified timestamps
    const ts = currentMetaEp?.timestamps?.ed
    if (ts?.start_s != null && ts?.end_s != null && ts.end_s > ts.start_s) {
      return { start_s: ts.start_s, end_s: ts.end_s, start_fmt: ts.start_fmt || formatSec(ts.start_s), end_fmt: ts.end_fmt || formatSec(ts.end_s) }
    }
    return null
  }, [streamData, currentMetaEp])

  // Auto-skip settings with persistence
  const [autoSkipOp, setAutoSkipOp] = useState(() => localStorage.getItem('animan_autoskip_op') === 'true')
  const [autoSkipEd, setAutoSkipEd] = useState(() => localStorage.getItem('animan_autoskip_ed') === 'true')

  const toggleAutoSkipOp = (val) => {
    setAutoSkipOp(val)
    localStorage.setItem('animan_autoskip_op', String(val))
  }
  const toggleAutoSkipEd = (val) => {
    setAutoSkipEd(val)
    localStorage.setItem('animan_autoskip_ed', String(val))
  }

  // Time update listener for skip overlays and automatic skip execution
  const handleTimeUpdate = () => {
    const video = videoRef.current
    if (!video) return
    const cur = video.currentTime
    setCurrentTime(cur)

    // Auto-skip opening
    if (autoSkipOp && opSkip && cur >= opSkip.start_s && cur < opSkip.start_s + 2) {
      video.currentTime = opSkip.end_s + 0.1
      return
    }
    // Auto-skip ending
    if (autoSkipEd && edSkip && cur >= edSkip.start_s && cur < edSkip.start_s + 2) {
      video.currentTime = edSkip.end_s + 0.1
      return
    }

    if (opSkip && cur >= opSkip.start_s && cur <= opSkip.end_s) {
      setShowOpSkip(true)
    } else {
      setShowOpSkip(false)
    }

    if (edSkip && cur >= edSkip.start_s && cur <= edSkip.end_s) {
      setShowEdSkip(true)
    } else {
      setShowEdSkip(false)
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setVideoDuration(videoRef.current.duration || 0)
    }
  }

  const handleVideoEnded = () => {
    setIsPlaying(false)
    if (autoNext) {
      const curIdx = availableEpNumbers.indexOf(activeEpNum)
      if (curIdx >= 0 && curIdx < availableEpNumbers.length - 1) {
        setActiveEpNum(availableEpNumbers[curIdx + 1])
      }
    }
  }

  const handleSkipOp = () => {
    if (videoRef.current && opSkip) {
      videoRef.current.currentTime = opSkip.end_s + 1
      setShowOpSkip(false)
    }
  }

  const handleSkipEd = () => {
    if (videoRef.current && edSkip) {
      videoRef.current.currentTime = edSkip.end_s + 1
      setShowEdSkip(false)
    }
  }

  const handleSeek = (e) => {
    if (!seekbarRef.current || !videoRef.current || !videoDuration) return
    const rect = seekbarRef.current.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const percent = Math.max(0, Math.min(1, clickX / rect.width))
    const target = percent * videoDuration
    videoRef.current.currentTime = target
    setCurrentTime(target)
  }

  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed)
    if (videoRef.current) {
      videoRef.current.playbackRate = speed
    }
  }

  // Ep counts for tabs
  const epCounts = useMemo(() => {
    let canon = 0, filler = 0, mixed = 0, anime_canon = 0
    for (const num of availableEpNumbers) {
      const meta = metaEpMap.get(num)
      const t = meta?.filler_type || 'canon'
      if (t === 'filler') filler++
      else if (t === 'mixed') mixed++
      else if (t === 'anime_canon') anime_canon++
      else canon++
    }
    return { canon, filler, mixed, anime_canon, total: availableEpNumbers.length }
  }, [availableEpNumbers, metaEpMap])

  // Filtered episodes list
  const filteredEpisodes = useMemo(() => {
    return availableEpNumbers.filter((epNum) => {
      const meta = metaEpMap.get(epNum)
      const t = meta?.filler_type || 'canon'
      if (filterType === 'canon') {
        if (t === 'filler') return false
      } else if (filterType === 'filler') {
        if (t !== 'filler') return false
      } else if (filterType === 'mixed') {
        if (t !== 'mixed' && t !== 'anime_canon') return false
      }
      if (epSearch) {
        const q = epSearch.toLowerCase().trim()
        const matchNum = String(epNum).includes(q)
        const matchTitle = (meta?.title_ru || meta?.title || meta?.title_en || '').toLowerCase().includes(q)
        return matchNum || matchTitle
      }
      return true
    })
  }, [availableEpNumbers, metaEpMap, filterType, epSearch])

  // Seekbar percentages
  const currentPercent = videoDuration > 0 ? (currentTime / videoDuration) * 100 : 0
  const opBarStart = opSkip && videoDuration > 0 ? (opSkip.start_s / videoDuration) * 100 : 0
  const opBarWidth = opSkip && videoDuration > 0 ? ((opSkip.end_s - opSkip.start_s) / videoDuration) * 100 : 0
  const edBarStart = edSkip && videoDuration > 0 ? (edSkip.start_s / videoDuration) * 100 : 0
  const edBarWidth = edSkip && videoDuration > 0 ? ((edSkip.end_s - edSkip.start_s) / videoDuration) * 100 : 0

  if (studios.length === 0) {
    return null
  }

  return (
    <div className={`ani-player-wrapper ${theaterMode ? 'theater-mode' : ''}`}>
      {/* Top Header Bar */}
      <div className="ani-player-header">
        <div className="ani-player-title-row">
          <span className="ani-player-badge">🎬 Онлайн плеер Kodik</span>
          <h3 className="ani-player-current-ep">
            Серия {activeEpNum}
            {currentMetaEp?.title_ru ? ` · ${currentMetaEp.title_ru}` : currentMetaEp?.title_en ? ` · ${currentMetaEp.title_en}` : ''}
          </h3>
          {currentMetaEp?.filler_type === 'filler' ? (
            <span className="ep-filler-pill ep-filler--filler">🔴 Филлер</span>
          ) : currentMetaEp?.filler_type === 'mixed' ? (
            <span className="ep-filler-pill ep-filler--mixed">🟡 Смешанный канон</span>
          ) : currentMetaEp?.filler_type === 'anime_canon' ? (
            <span className="ep-filler-pill ep-filler--anime_canon">🔵 Аниме-канон</span>
          ) : (
            <span className="ep-filler-pill ep-filler--canon">🟢 Канон манги</span>
          )}
        </div>

        <div className="ani-player-header-actions">
          {/* Mode Switcher: HLS Direct Stream vs Kodik Iframe */}
          <div className="player-mode-switch">
            <button
              type="button"
              className={`btn-player-mode ${playerMode === 'hls' ? 'active' : ''}`}
              onClick={() => setPlayerMode('hls')}
              title="Прямой видеопоток HLS"
            >
              ⚡ Прямой поток (HLS)
            </button>
            <button
              type="button"
              className={`btn-player-mode ${playerMode === 'iframe' ? 'active' : ''}`}
              onClick={() => setPlayerMode('iframe')}
              title="Встроенный плеер Kodik (если не воспроизводится прямой поток)"
            >
              🗖 Плеер Kodik
            </button>
          </div>

          <button
            type="button"
            className={`btn-player-mode ${theaterMode ? 'active' : ''}`}
            onClick={() => setTheaterMode(!theaterMode)}
            title="Кинотеатральный режим"
          >
            {theaterMode ? '🗗 Обычный вид' : '🗖 Кинотеатр'}
          </button>
        </div>
      </div>

      {/* Main Layout: Video Screen + Right Sidebar */}
      <div className="ani-player-main-layout">
        {/* Left Video Col */}
        <div className="ani-player-screen-col">
          <div className="ani-video-container">
            {resolving ? (
              <div className="ani-player-no-video">
                <div className="loading-spinner" />
                <div className="no-video-title">Загрузка видеопотока Kodik…</div>
                <div className="no-video-subtitle">Резолвим прямой HLS поток и таймкоды серии {activeEpNum}</div>
              </div>
            ) : playerMode === 'iframe' || !currentDirectUrl ? (
              /* Fallback to Kodik Embed Iframe */
              currentEpEntry?.link ? (
                <iframe
                  src={currentEpEntry.link}
                  className="ani-iframe-element"
                  width="100%"
                  height="100%"
                  frameBorder="0"
                  allowFullScreen
                  allow="autoplay *; fullscreen *"
                  title={`Kodik Player - Серия ${activeEpNum}`}
                />
              ) : (
                <div className="ani-player-no-video">
                  <div className="no-video-icon">🎬</div>
                  <div className="no-video-title">Серия не найдена</div>
                </div>
              )
            ) : (
              /* Native HLS Video Element */
              <>
                <video
                  ref={videoRef}
                  className="ani-video-element"
                  controls
                  playsInline
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onEnded={handleVideoEnded}
                />

                {/* Floating AniSkip Overlay Buttons */}
                {showOpSkip && opSkip ? (
                  <button type="button" className="aniskip-overlay-btn aniskip-op" onClick={handleSkipOp}>
                    <span className="aniskip-icon">⏩</span>
                    <span>Пропустить опенинг ({opSkip.start_fmt} → {opSkip.end_fmt})</span>
                  </button>
                ) : null}

                {showEdSkip && edSkip ? (
                  <button type="button" className="aniskip-overlay-btn aniskip-ed" onClick={handleSkipEd}>
                    <span className="aniskip-icon">⏩</span>
                    <span>Пропустить эндинг ({edSkip.start_fmt} → {edSkip.end_fmt})</span>
                  </button>
                ) : null}
              </>
            )}
          </div>

          {/* Interactive Seekbar Timeline with AniSkip Glow Markers */}
          {playerMode === 'hls' && videoDuration > 0 ? (
            <div className="ani-timeline-container">
              <div className="ani-seekbar-bar" ref={seekbarRef} onClick={handleSeek}>
                <div className="seekbar-track" />
                {opSkip && opBarWidth > 0 ? (
                  <div
                    className="seekbar-range-marker op-marker"
                    style={{ left: `${opBarStart}%`, width: `${opBarWidth}%` }}
                    title={`Опенинг: ${opSkip.start_fmt} - ${opSkip.end_fmt}`}
                  >
                    <span className="range-tag">OP</span>
                  </div>
                ) : null}
                {edSkip && edBarWidth > 0 ? (
                  <div
                    className="seekbar-range-marker ed-marker"
                    style={{ left: `${edBarStart}%`, width: `${edBarWidth}%` }}
                    title={`Эндинг: ${edSkip.start_fmt} - ${edSkip.end_fmt}`}
                  >
                    <span className="range-tag">ED</span>
                  </div>
                ) : null}
                <div className="seekbar-progress" style={{ width: `${currentPercent}%` }} />
              </div>

              <div className="timeline-time-row">
                <span className="time-curr">{formatSec(currentTime)}</span>
                <span className="time-dur">{formatSec(videoDuration)}</span>
              </div>
            </div>
          ) : null}

          {/* Sub Controls: Quick Skips, Speed, Quality, Auto-next */}
          <div className="ani-player-sub-bar">
            <div className="ani-sub-bar-left">
              {opSkip ? (
                <button type="button" className="btn-quick-skip op" onClick={handleSkipOp} title="Пропустить опенинг">
                  ⏩ OP ({opSkip.start_fmt} → {opSkip.end_fmt})
                </button>
              ) : null}
              {edSkip ? (
                <button type="button" className="btn-quick-skip ed" onClick={handleSkipEd} title="Пропустить эндинг">
                  ⏩ ED ({edSkip.start_fmt} → {edSkip.end_fmt})
                </button>
              ) : null}
            </div>

            <div className="ani-sub-bar-right">
              {/* Playback Speed */}
              {playerMode === 'hls' ? (
                <div className="player-speed-select-wrap">
                  <span className="sub-bar-label">Скорость:</span>
                  {[0.75, 1, 1.25, 1.5, 2].map((spd) => (
                    <button
                      key={spd}
                      type="button"
                      className={`btn-speed-chip ${playbackSpeed === spd ? 'active' : ''}`}
                      onClick={() => handleSpeedChange(spd)}
                    >
                      {spd}x
                    </button>
                  ))}
                </div>
              ) : null}

              {/* Auto Skip OP / ED */}
              <label className="player-autonext-label" title="Автоматически пропускать заставку (опенинг)">
                <input
                  type="checkbox"
                  checked={autoSkipOp}
                  onChange={(e) => toggleAutoSkipOp(e.target.checked)}
                />
                <span>Авто OP</span>
              </label>

              <label className="player-autonext-label" title="Автоматически пропускать финальные титры (эндинг)">
                <input
                  type="checkbox"
                  checked={autoSkipEd}
                  onChange={(e) => toggleAutoSkipEd(e.target.checked)}
                />
                <span>Авто ED</span>
              </label>

              {/* Auto Next */}
              <label className="player-autonext-label">
                <input
                  type="checkbox"
                  checked={autoNext}
                  onChange={(e) => setAutoNext(e.target.checked)}
                />
                <span>Автопереход</span>
              </label>
            </div>
          </div>
        </div>

        {/* Right Sidebar: Voiceover Studios & Quality Selection */}
        <div className="ani-player-sidebar">
          {/* Studio / Fandub Selection */}
          <div className="sidebar-group">
            <div className="sidebar-group-title">
              <span>🎙️ Озвучка / Фандаб</span>
              <span className="sidebar-count">{studios.length} доступно</span>
            </div>
            <div className="fandub-chips-grid">
              {studios.map((sName) => {
                const stObj = kodikCatalog[sName]
                const isSelected = activeStudio === sName
                return (
                  <button
                    key={sName}
                    type="button"
                    className={`fandub-chip-btn ${isSelected ? 'active' : ''}`}
                    onClick={() => setActiveStudio(sName)}
                  >
                    <span className="fandub-name">{sName}</span>
                    <span className="fandub-type-badge">
                      {stObj?.type === 'subtitles' ? 'Субтитры' : `${stObj?.episodes_count || 0} сер.`}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Quality Switcher (when stream links available) */}
          {playerMode === 'hls' && streamData?.links ? (
            <div className="sidebar-group">
              <div className="sidebar-group-title">
                <span>📺 Качество видео</span>
              </div>
              <div className="quality-chips-row">
                {Object.keys(streamData.links).map((q) => (
                  <button
                    key={q}
                    type="button"
                    className={`quality-chip-btn ${activeQuality === q ? 'active' : ''}`}
                    onClick={() => setActiveQuality(q)}
                  >
                    <span className="quality-val">{q}p</span>
                    <span className="quality-label">
                      {q === '1080' ? 'Full HD' : q === '720' ? 'HD' : 'SD'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {/* Quick Stepper Navigation */}
          <div className="sidebar-group">
            <div className="sidebar-group-title">
              <span>⚡ Навигация</span>
            </div>
            <div className="ep-nav-buttons-row">
              <button
                type="button"
                className="btn-ep-nav"
                disabled={availableEpNumbers.indexOf(activeEpNum) <= 0}
                onClick={() => {
                  const idx = availableEpNumbers.indexOf(activeEpNum)
                  if (idx > 0) setActiveEpNum(availableEpNumbers[idx - 1])
                }}
              >
                ◀ Предыдущая
              </button>
              <button
                type="button"
                className="btn-ep-nav"
                disabled={availableEpNumbers.indexOf(activeEpNum) >= availableEpNumbers.length - 1}
                onClick={() => {
                  const idx = availableEpNumbers.indexOf(activeEpNum)
                  if (idx < availableEpNumbers.length - 1) setActiveEpNum(availableEpNumbers[idx + 1])
                }}
              >
                Следующая ▶
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Episode Selection Section (Grid / List) */}
      <div className="ani-episodes-section">
        <div className="episodes-sec-head">
          <div className="ep-head-left">
            <h3 className="episodes-sec-title">📑 Список эпизодов</h3>
            <span className="ep-total-count">{availableEpNumbers.length} серий в озвучке</span>
          </div>

          <div className="ep-head-controls">
            {/* Filter Tabs */}
            <div className="ep-filter-tabs">
              <button
                type="button"
                className={`ep-filter-btn ${filterType === 'all' ? 'active' : ''}`}
                onClick={() => setFilterType('all')}
              >
                Все ({availableEpNumbers.length})
              </button>
              <button
                type="button"
                className={`ep-filter-btn ${filterType === 'canon' ? 'active' : ''}`}
                onClick={() => setFilterType('canon')}
              >
                🟢 Канон ({epCounts.canon})
              </button>
              {epCounts.filler > 0 ? (
                <button
                  type="button"
                  className={`ep-filter-btn ep-filter-btn--filler ${filterType === 'filler' ? 'active' : ''}`}
                  onClick={() => setFilterType('filler')}
                >
                  🔴 Филлеры ({epCounts.filler})
                </button>
              ) : null}
              {epCounts.mixed > 0 || epCounts.anime_canon > 0 ? (
                <button
                  type="button"
                  className={`ep-filter-btn ep-filter-btn--mixed ${filterType === 'mixed' ? 'active' : ''}`}
                  onClick={() => setFilterType('mixed')}
                >
                  🟡 Смешанные ({epCounts.mixed + epCounts.anime_canon})
                </button>
              ) : null}
            </div>

            {/* Quick Search */}
            <input
              type="text"
              className="ep-search-input"
              placeholder="🔍 Номер или название серии..."
              value={epSearch}
              onChange={(e) => setEpSearch(e.target.value)}
            />

            {/* View Mode Toggle */}
            <div className="ep-view-mode-toggle">
              <button
                type="button"
                className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                title="Сетка номеров"
              >
                ▦
              </button>
              <button
                type="button"
                className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
                title="Список с превью"
              >
                ☰
              </button>
            </div>
          </div>
        </div>

        {/* View Mode: Numbers Grid */}
        {viewMode === 'grid' ? (
          <div className="ep-numbers-grid">
            {filteredEpisodes.map((epNum) => {
              const isCurrent = epNum === activeEpNum
              const meta = metaEpMap.get(epNum)
              const fType = meta?.filler_type || 'canon'
              return (
                <button
                  key={epNum}
                  type="button"
                  className={`ep-num-card ${isCurrent ? 'current' : ''} ${fType}`}
                  onClick={() => setActiveEpNum(epNum)}
                  title={`Серия ${epNum}: ${meta?.filler_label || 'Канон'}${meta?.title_en ? ` (${meta.title_en})` : ''}`}
                >
                  <span className="ep-num-val">{epNum}</span>
                  {fType === 'filler' ? (
                    <span className="ep-num-filler-dot" title="Филлер" />
                  ) : fType === 'mixed' ? (
                    <span className="ep-num-mixed-dot" title="Смешанный канон" />
                  ) : null}
                </button>
              )
            })}
          </div>
        ) : (
          /* View Mode: Detailed List with Thumbnails */
          <div className="ep-detailed-list">
            {filteredEpisodes.map((epNum) => {
              const isCurrent = epNum === activeEpNum
              const meta = metaEpMap.get(epNum)
              const kodikEp = currentEpisodesDict[String(epNum)]
              const thumb = kodikEp?.screenshots?.[0] || meta?.thumbnail
              const fType = meta?.filler_type || 'canon'

              return (
                <div
                  key={epNum}
                  className={`ep-list-card ${isCurrent ? 'current' : ''} ep-list--${fType}`}
                  onClick={() => setActiveEpNum(epNum)}
                >
                  <div className="ep-list-thumb-wrap">
                    {thumb ? (
                      <img src={thumb} alt={`Серия ${epNum}`} className="ep-list-thumb" loading="lazy" />
                    ) : (
                      <div className="ep-list-thumb-placeholder">#{epNum}</div>
                    )}
                    <span className="ep-list-num-badge">№ {epNum}</span>
                  </div>

                  <div className="ep-list-info">
                    <div className="ep-list-title-row">
                      <h4 className="ep-list-title">
                        {meta?.title_ru || meta?.title_en || `Серия ${epNum}`}
                      </h4>
                      {meta?.filler_label ? (
                        <span className={`ep-filler-pill ep-filler--${fType}`}>
                          {meta.filler_label}
                        </span>
                      ) : null}
                    </div>

                    {meta?.title_en && meta.title_en !== meta.title_ru ? (
                      <div className="ep-list-en-title">{meta.title_en}</div>
                    ) : null}

                    {meta?.timestamps?.op ? (
                      <div className="ep-list-skip-badge">
                        ✨ AniSkip: Опенинг ({meta.timestamps.op.start_fmt || '00:57'} → {meta.timestamps.op.end_fmt || '02:26'})
                      </div>
                    ) : null}
                  </div>

                  <div className="ep-list-play-action">
                    <button type="button" className="btn-play-ep">
                      {isCurrent ? '▶ Играет' : 'Смотреть'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
