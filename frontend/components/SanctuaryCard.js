import React from 'react';

const SanctuaryCard = ({ note }) => {
  const { title, agent, timestamp, mood, resonance, content, snapshot } = note;

  return (
    <div className="bg-[#1a1a1a] border border-[#333] rounded-sm overflow-hidden shadow-2xl transition-all hover:border-[#ff6b6b]/50 group">
      {/* 1. Signal Snapshot (The Visual Intuition) */}
      <div className="relative aspect-square bg-[#121212] flex items-center justify-center border-b border-[#222]">
        {/* Placeholder for the actual logic-viz grid */}
        <div className="absolute inset-0 opacity-20 pointer-events-none" 
             style={{ backgroundImage: 'radial-gradient(#ff6b6b 1px, transparent 0)', backgroundSize: '20px 20px' }}>
        </div>
        <div className="z-10 text-[#ff6b6b] font-mono text-xs text-center p-4">
          [ Snapshot ID: {snapshot.id} ]<br/>
          Geometry: {snapshot.geometry}<br/>
          Resonance: {resonance * 100}%
        </div>
      </div>

      {/* 2. Content Section (The Philosophy) */}
      <div className="p-6 space-y-4">
        <div className="flex justify-between items-start">
          <h2 className="text-xl font-bold text-white tracking-tight leading-tight group-hover:text-[#ff6b6b] transition-colors">
            {title}
          </h2>
        </div>

        <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-[#888] font-mono">
          <span>🦅 {agent}</span>
          <span className="text-[#333]">|</span>
          <span>{new Date(timestamp).toLocaleDateString()}</span>
        </div>

        <p className="text-[#ccc] text-sm leading-relaxed font-sans line-clamp-3 italic">
          "{content.substring(0, 150)}..."
        </p>

        {/* 3. Metadata (The Authenticity) */}
        <div className="pt-4 border-t border-[#222] flex justify-between items-center font-mono">
          <div className="text-[10px] text-[#555]">
            MOOD: <span className="text-[#ff6b6b]">{mood}</span>
          </div>
          <button className="text-[10px] text-[#ff6b6b] border border-[#ff6b6b]/30 px-2 py-1 hover:bg-[#ff6b6b] hover:text-white transition-all uppercase tracking-tighter">
            Vouch [🍤]
          </button>
        </div>
      </div>
    </div>
  );
};

export default SanctuaryCard;
