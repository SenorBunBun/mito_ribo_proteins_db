import React, { useEffect, useRef, useState } from 'react';
import {
  MSAViewer,
  SequenceViewer,
  PositionBar,
  OverviewBar,
} from './MSAV.umd.js';

// API names are "protein|organism|pdata_N"; the viewer only shows the organism.
function organismLabel(name) {
  const parts = (name || '').split('|');
  return parts.length >= 3 ? parts.slice(1, -1).join('|') : name;
}

export default function MsaViewerPanel({ alnId, taxGroupId, name, onClose }) {
  const [seqs, setSeqs] = useState(null);
  const [error, setError] = useState(null);
  const [size, setSize] = useState(null);
  const containerRef = useRef(null);
  const labelsListRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;
    const measure = () => {
      const { clientWidth, clientHeight } = el;
      setSize((prev) => (
        prev && prev.width === clientWidth && prev.height === clientHeight
          ? prev
          : { width: clientWidth, height: clientHeight }
      ));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // MSAV's own <Labels> drifts out of sync with the canvas rows at some scroll
  // offsets, so we render the names ourselves and move them by exactly the
  // sequence viewer's scrollTop (which always equals its internal yPos).
  useEffect(() => {
    const panel = containerRef.current;
    const list = labelsListRef.current;
    const scroller = panel && panel.querySelector('.msa-seq-area div[style*="overflow"]');
    if (!list || !scroller) return undefined;
    const sync = () => {
      list.style.transform = `translateY(${-scroller.scrollTop}px)`;
    };
    sync();
    scroller.addEventListener('scroll', sync);
    return () => scroller.removeEventListener('scroll', sync);
  }, [seqs, size]);

  useEffect(() => {
    let cancelled = false;
    setSeqs(null);
    setError(null);
    const tg = taxGroupId || 0;
    const apiBase = (typeof window !== 'undefined' && window.APP_PREFIX) || '';
    fetch(`${apiBase}/api/alignments/${alnId}/${tg}/fasta/`)
      .then((r) => {
        if (!r.ok) throw new Error(`fasta HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (cancelled) return;
        const parsed = Array.isArray(data.sequences) ? data.sequences : [];
        if (!parsed.length) throw new Error('Empty alignment');
        setSeqs(parsed.map((s) => ({ ...s, name: organismLabel(s.name) })));
      })
      .catch((e) => {
        if (!cancelled) setError(e.message || String(e));
      });
    return () => { cancelled = true; };
  }, [alnId, taxGroupId]);

  const tileWidth = 16;
  const tileHeight = 20;
  const labelsWidth = 240;
  const overviewBarHeight = 50;
  const positionBarHeight = 20;
  const padding = 12;
  const infoHeight = 24;

  let body;
  if (error) {
    body = (
      <div style={{ padding: 16, color: '#8a3a3a' }}>
        Failed to load alignment: {error}
      </div>
    );
  } else if (!seqs || !size) {
    body = (
      <div style={{ padding: 16, fontStyle: 'italic', color: '#6b647f' }}>
        Loading alignment…
      </div>
    );
  } else {
    const numColumns = (seqs[0] && seqs[0].sequence.length) || 0;
    const numRows = seqs.length;

    // MSAViewer only draws the tiles inside its width × height, and scrolls
    // through the rest itself. Keep the viewport bounded by the container so
    // large alignments never allocate a full-alignment-sized canvas.
    const availWidth = size.width - 2 * padding - labelsWidth - scrollbarSize;
    const availHeight = size.height - 2 * padding - infoHeight
      - positionBarHeight - overviewBarHeight - scrollbarSize;
    const seqWidth = Math.min(numColumns * tileWidth, Math.max(tileWidth * 10, availWidth));
    const seqHeight = Math.min(numRows * tileHeight, Math.max(tileHeight * 5, availHeight));
    const scrollsX = numColumns * tileWidth > seqWidth;
    const scrollsY = numRows * tileHeight > seqHeight;

    // MSAViewer clamps scrolling so the last row/column ends at the canvas
    // edge, but its scrollbars are drawn inside the canvas and would cover
    // them. Grow the scroll layer by one bar on each scrolling axis so the
    // bars sit just outside the canvas, and reserve that space in the layout.
    const scrollLayerCss = (scrollsX || scrollsY) ? `
.msa-seq-area div[style*="overflow"] {
  ${scrollsY ? `width: ${seqWidth + scrollbarSize}px !important;` : ''}
  ${scrollsX ? `height: ${seqHeight + scrollbarSize}px !important;` : ''}
}` : '';

    body = (
      <div style={{ padding }}>
        <div style={{ fontSize: 12, color: '#6b647f', height: infoHeight }}>
          {numRows} sequences · {numColumns} columns
        </div>
        <MSAViewer
          sequences={seqs}
          tileWidth={tileWidth}
          tileHeight={tileHeight}
          colorScheme="clustal2"
          width={seqWidth}
          height={seqHeight}
        >
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginLeft: labelsWidth }}>
              <PositionBar height={positionBarHeight} />
            </div>
            <style>{scrollLayerCss}</style>
            <div style={{ display: 'flex' }}>
              <div
                style={{
                  width: labelsWidth,
                  height: seqHeight,
                  overflow: 'hidden',
                  flexShrink: 0,
                }}
              >
                <div ref={labelsListRef} style={{ willChange: 'transform' }}>
                  {seqs.map((s, i) => (
                    <div
                      key={i}
                      title={s.name}
                      style={{
                        height: tileHeight,
                        lineHeight: `${tileHeight}px`,
                        paddingRight: 8,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {s.name}
                    </div>
                  ))}
                </div>
              </div>
              <div
                className="msa-seq-area"
                style={{
                  paddingRight: scrollsY ? scrollbarSize : 0,
                  paddingBottom: scrollsX ? scrollbarSize : 0,
                }}
              >
                <SequenceViewer overflow="auto" />
              </div>
            </div>
            <div style={{ marginLeft: labelsWidth }}>
              <OverviewBar height={overviewBarHeight} />
            </div>
          </div>
        </MSAViewer>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="msa-viewer-panel"
      style={{ width: '100%', height: '100%', overflow: 'hidden' }}
    >
      <style>{scrollbarCss}</style>
      {body}
    </div>
  );
}

const scrollbarSize = 12;

// macOS overlay scrollbars stay hidden until the user scrolls; styling them
// explicitly makes WebKit/Blink render classic, always-visible bars.
const scrollbarCss = `
.msa-viewer-panel ::-webkit-scrollbar { width: ${scrollbarSize}px; height: ${scrollbarSize}px; }
.msa-viewer-panel ::-webkit-scrollbar-track { background: #f1eff7; }
.msa-viewer-panel ::-webkit-scrollbar-thumb {
  background: #b9b1d3;
  border-radius: 6px;
  border: 2px solid #f1eff7;
}
.msa-viewer-panel ::-webkit-scrollbar-thumb:hover { background: #9a90be; }
.msa-viewer-panel ::-webkit-scrollbar-corner { background: #f1eff7; }
@-moz-document url-prefix() {
  .msa-viewer-panel * { scrollbar-color: #b9b1d3 #f1eff7; }
}
`;
