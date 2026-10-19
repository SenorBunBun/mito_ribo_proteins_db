import React, { useEffect, useRef, useState } from 'react';
import {
  MSAViewer,
  SequenceViewer,
  Labels,
  PositionBar,
  OverviewBar,
} from './MSAV.umd.js';

export default function MsaViewerPanel({ alnId, taxGroupId, name, onClose }) {
  const [seqs, setSeqs] = useState(null);
  const [error, setError] = useState(null);
  const [size, setSize] = useState(null);
  const containerRef = useRef(null);

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
        setSeqs(parsed);
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
    const availWidth = size.width - 2 * padding - labelsWidth;
    const availHeight = size.height - 2 * padding - infoHeight
      - positionBarHeight - overviewBarHeight;
    const seqWidth = Math.min(numColumns * tileWidth, Math.max(tileWidth * 10, availWidth));
    const seqHeight = Math.min(numRows * tileHeight, Math.max(tileHeight * 5, availHeight));

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
            <div style={{ display: 'flex' }}>
              <Labels style={{ width: labelsWidth }} />
              <SequenceViewer overflow="auto" />
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
    <div ref={containerRef} style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      {body}
    </div>
  );
}
