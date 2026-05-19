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
  const labelsWidth = 220;
  const gridHeight = Math.min(seqs.length * tileHeight + tileHeight, 560);

  return (
    <div style={{ padding: 12 }}>
      <div style={{ fontSize: 12, color: '#6b647f', marginBottom: 8 }}>
        {seqs.length} sequences · {(seqs[0] && seqs[0].sequence.length) || 0} columns
      </div>
      <MSAViewer
        sequences={seqs}
        tileWidth={tileWidth}
        tileHeight={tileHeight}
        colorScheme="clustal2"
        height={gridHeight}
      >
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginLeft: labelsWidth }}>
            <OverviewBar />
            <PositionBar />
          </div>
          <div style={{ display: 'flex' }}>
            <Labels style={{ width: labelsWidth }} />
            <SequenceViewer />
          </div>
        </div>
      </MSAViewer>
    </div>
  );
}
