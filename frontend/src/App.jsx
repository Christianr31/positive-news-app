import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Globe from 'globe.gl'
import axios from 'axios'
import * as THREE from 'three'

const API_BASE = 'http://127.0.0.1:8000'

function storyKey(story, index) {
  return story.id || story.location_id || `story-${index}`
}

function StoryThumbCard({ story, variant = 'side' }) {
  const href = story.url?.trim() || undefined
  const title = story.title || 'Positive update'
  const locationLabel =
    story.city && story.country ? `${story.city}, ${story.country}` : null
  const imageUrl = story.image_url?.trim() || null
  const [imgFailed, setImgFailed] = useState(false)
  const hasImage = Boolean(imageUrl) && !imgFailed

  const inner = (
    <>
      <div className={`thumb-media ${variant}`}>
        {hasImage ? (
          <img
            src={imageUrl}
            alt={title}
            loading="lazy"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="thumb-placeholder" aria-hidden="true" />
        )}
      </div>
      <h3 className="thumb-title">{title}</h3>
      {variant === 'side' && locationLabel ? (
        <p className="thumb-sub">{locationLabel}</p>
      ) : null}
    </>
  )

  if (href) {
    return (
      <a
        className={`yt-card ${variant}`}
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        title={title}
      >
        {inner}
      </a>
    )
  }

  return <article className={`yt-card ${variant}`}>{inner}</article>
}

function App() {
  const globeEl = useRef(null)
  const globeInstance = useRef(null)
  const sidebarListRef = useRef(null)
  const ignoreNextPanelClick = useRef(false)
  const [weeklyHighlights, setWeeklyHighlights] = useState([])
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [locationStories, setLocationStories] = useState([])
  const [liveDataEnabled, setLiveDataEnabled] = useState(false)
  const [mode, setMode] = useState('general')
  const [sideStartIndex, setSideStartIndex] = useState(0)
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')

  const globeSurfacePoints = useMemo(() => {
    const surfaceColor =
      theme === 'dark' ? 'rgba(110, 231, 183, 0.26)' : 'rgba(22, 163, 74, 0.2)'
    const points = []
    for (let lat = -87; lat <= 87; lat += 6) {
      for (let lng = -180; lng <= 180; lng += 6) {
        points.push({
          id: `surface-${lat}-${lng}`,
          lat,
          lng,
          size: 0.004,
          color: surfaceColor,
          kind: 'surface',
        })
      }
    }
    return points
  }, [theme])

  const activeStories = mode === 'general' ? weeklyHighlights : locationStories
  const AHEAD_OFFSET = 3

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const fitGlobe = useCallback(() => {
    const globe = globeInstance.current
    const el = globeEl.current
    if (!globe || !el) return

    const width = el.clientWidth
    const height = el.clientHeight
    if (width > 0 && height > 0) {
      globe.width(width)
      globe.height(height)
    }
    globe.pointOfView({ lat: 18, lng: 0, altitude: 2.15 }, 0)
  }, [])

  useEffect(() => {
    const loadWeeklyHighlights = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/news/weekly-highlights`)
        setWeeklyHighlights(response.data.highlights)
        setLiveDataEnabled(Boolean(response.data.live_data_enabled))
      } catch (error) {
        console.error('Failed to load weekly highlights:', error)
      }
    }

    loadWeeklyHighlights()
  }, [])

  const markers = useMemo(
    () =>
      weeklyHighlights.map((item) => ({
        ...item,
        id: item.location_id,
        size: 0.22,
        color: theme === 'dark' ? '#34d399' : '#16a34a',
        kind: 'story',
      })),
    [theme, weeklyHighlights],
  )

  const handleLocationClick = useCallback(async (location) => {
    try {
      setSelectedLocation(location)
      setMode('regional')
      const response = await axios.get(`${API_BASE}/api/news/location-stories`, {
        params: { location_id: location.location_id },
      })
      setLocationStories(response.data.stories)
      setLiveDataEnabled(Boolean(response.data.live_data_enabled))
    } catch (error) {
      console.error('Failed to load stories for location:', error)
      setLocationStories([])
    }
  }, [])

  useEffect(() => {
    if (!globeEl.current || globeInstance.current) {
      return
    }

    const globe = Globe()(globeEl.current)
      .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
      .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundColor('rgba(0,0,0,0)')
      .pointAltitude('size')
      .pointColor('color')
      .pointRadius(0.32)
      .pointLabel((d) =>
        d.kind === 'story' ? `${d.city}, ${d.country}` : '',
      )
      .onPointClick((point) => {
        if (point.kind === 'story') {
          ignoreNextPanelClick.current = true
          setTimeout(() => {
            ignoreNextPanelClick.current = false
          }, 0)
          handleLocationClick(point)
        }
      })

    globe.controls().autoRotate = true
    globe.controls().autoRotateSpeed = 0.35
    globe.controls().enableDamping = true
    globe.controls().dampingFactor = 0.06
    globe.atmosphereColor('#6ee7b7')
    globe.atmosphereAltitude(0.2)

    globeInstance.current = globe
    fitGlobe()

    window.addEventListener('resize', fitGlobe)

    return () => {
      window.removeEventListener('resize', fitGlobe)
    }
  }, [fitGlobe, handleLocationClick])

  useEffect(() => {
    if (!globeInstance.current) return
    globeInstance.current.pointsData([...globeSurfacePoints, ...markers])
  }, [markers, globeSurfacePoints])

  useEffect(() => {
    const globe = globeInstance.current
    if (!globe) return

    globe.atmosphereColor(theme === 'dark' ? '#6ee7b7' : '#67e8f9')
    globe.backgroundColor('rgba(0,0,0,0)')
  }, [theme])

  useEffect(() => {
    fitGlobe()
  }, [fitGlobe, mode])

  const goGeneral = () => {
    setSelectedLocation(null)
    setLocationStories([])
    setMode('general')
    setSideStartIndex(0)
    if (sidebarListRef.current) {
      sidebarListRef.current.scrollTop = 0
    }
  }

  const handleSidebarScroll = useCallback(() => {
    const list = sidebarListRef.current
    if (!list) return
    const firstCard = list.firstElementChild
    if (!firstCard) {
      setSideStartIndex(0)
      return
    }
    const styles = window.getComputedStyle(list)
    const gap = Number.parseFloat(styles.rowGap || styles.gap || '0') || 0
    const cardStep = firstCard.getBoundingClientRect().height + gap
    if (cardStep <= 0) {
      setSideStartIndex(0)
      return
    }
    setSideStartIndex(Math.max(0, Math.floor(list.scrollTop / cardStep)))
  }, [])

  useEffect(() => {
    setSideStartIndex(0)
    if (sidebarListRef.current) {
      sidebarListRef.current.scrollTop = 0
    }
  }, [mode, selectedLocation?.location_id])

  const bottomStories = useMemo(() => {
    if (activeStories.length === 0) return []
    const start = (sideStartIndex + AHEAD_OFFSET) % activeStories.length
    return [...activeStories.slice(start), ...activeStories.slice(0, start)]
  }, [activeStories, sideStartIndex])

  const panelTitle =
    mode === 'general'
      ? 'Top stories this week'
      : selectedLocation
        ? `${selectedLocation.city} stories`
        : 'Regional stories'

  const bottomTitle =
    mode === 'general' ? 'More positive news' : `More from ${selectedLocation?.city || 'this region'}`

  return (
    <div className="app-shell">
      <header className="top-bar">
        <h1>Positive News</h1>
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
        >
          {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
      </header>

      <div className="main-stage">
        <section
          className="globe-panel"
          onClick={() => {
            if (!ignoreNextPanelClick.current && mode === 'regional') {
              goGeneral()
            }
          }}
        >
          <div className="globe-frame">
            <div ref={globeEl} className="globe-canvas" />
          </div>
        </section>

        <aside className="stories-panel">
          <div className="panel-top">
            <div className={`status-pill ${liveDataEnabled ? 'live' : 'fallback'}`}>
              {liveDataEnabled ? 'Live sources' : 'Demo fallback'}
            </div>
            <div className="mode-toggle">
              <button
                type="button"
                className={`toggle-btn ${mode === 'general' ? 'active' : ''}`}
                onClick={goGeneral}
              >
                General
              </button>
              <button
                type="button"
                className={`toggle-btn ${mode === 'regional' ? 'active' : ''}`}
                disabled={!selectedLocation}
                onClick={() => setMode('regional')}
              >
                Regional
              </button>
            </div>
          </div>

          <h2 className="panel-heading">{panelTitle}</h2>

          <div
            ref={sidebarListRef}
            className="sidebar-card-list"
            onScroll={handleSidebarScroll}
          >
            {activeStories.length > 0 ? (
              activeStories.map((story, index) => (
                <StoryThumbCard
                  key={storyKey(story, index)}
                  story={story}
                  variant="side"
                />
              ))
            ) : (
              <p className="empty-hint">
                Click a bright marker on the globe for regional stories.
              </p>
            )}
          </div>
        </aside>
      </div>

      <section className="bottom-rail">
        <h2 className="rail-heading">{bottomTitle}</h2>
        <div className="bottom-card-row">
          {bottomStories.length > 0 ? (
            bottomStories.map((story, index) => (
              <StoryThumbCard
                key={`bottom-${storyKey(story, index)}`}
                story={story}
                variant="bottom"
              />
            ))
          ) : (
            <p className="empty-hint">Stories will appear here.</p>
          )}
        </div>
      </section>
    </div>
  )
}

export default App
