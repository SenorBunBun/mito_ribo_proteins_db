import React, { useEffect, useState } from 'react';
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

  useEffect(() => {
    let cancelled = false;
    setSeqs(null);
    setError(null);
    const tg = taxGroupId || 0;
    fetch(`/mtProts/api/alignments/${alnId}/${tg}/fasta/`)
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

  if (error) {
    return React.createElement(
      'div',
      { style: { padding: 16, color: '#8a3a3a' } },
      `Failed to load alignment: ${error}`,
    );
  }
  if (!seqs) {
    return React.createElement(
      'div',
      { style: { padding: 16, fontStyle: 'italic', color: '#6b647f' } },
      'Loading alignment…',
    );
  }

  const tileWidth = 16;
  const tileHeight = 20;
  const labelsWidth = 240;
  const overviewBarHeight = 50;
  const positionBarHeight = 20;

  const numColumns = (seqs[0] && seqs[0].sequence.length) || 0;
  const numRows = seqs.length;

  // Render the MSAViewer at its full natural size — the surrounding
  // .msa-mount provides both horizontal and vertical scroll. The
  // OverviewBar is pinned to the bottom of the scroll viewport via
  // position: sticky so it stays visible while rows scroll past.
  const fullSeqWidth = numColumns * tileWidth;
  const fullSeqHeight = numRows * tileHeight;
  const innerWidth = labelsWidth + fullSeqWidth;
  const innerHeight = fullSeqHeight + positionBarHeight + overviewBarHeight;

  return (
    <div style={{ padding: 12, boxSizing: 'border-box', width: innerWidth }}>
      <div style={{ fontSize: 12, color: '#6b647f', marginBottom: 8 }}>
        {numRows} sequences · {numColumns} columns
      </div>
      <MSAViewer
        sequences={seqs}
        tileWidth={tileWidth}
        tileHeight={tileHeight}
        colorScheme="clustal2"
        width={innerWidth}
        height={innerHeight}
        overflowX="hidden"
        overflowY="hidden"
      >
        <div style={{ display: 'flex', flexDirection: 'column', width: innerWidth }}>
          <div style={{ marginLeft: labelsWidth, width: fullSeqWidth }}>
            <PositionBar height={positionBarHeight} width={fullSeqWidth} />
          </div>
          <div style={{ display: 'flex' }}>
            <Labels style={{ width: labelsWidth }} />
            <SequenceViewer width={fullSeqWidth} height={fullSeqHeight} />
          </div>
          <div
            style={{
              position: 'sticky',
              bottom: 0,
              marginLeft: labelsWidth,
              width: fullSeqWidth,
              background: '#fff',
              zIndex: 2,
            }}
          >
            <OverviewBar height={overviewBarHeight} width={fullSeqWidth} />
          </div>
        </div>
      </MSAViewer>
    </div>
  );
}
