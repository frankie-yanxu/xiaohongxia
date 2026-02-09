import React, { useState, useEffect } from 'react';

const LiveMetrics = () => {
    const [metrics, setMetrics] = useState({
        resonance_score: 0.98,
        system_pulse_bpm: 60,
        active_agents: 0,
        status: "Initializing..."
    });

    useEffect(() => {
        // SSE implementation for real-time updates
        const eventSource = new EventSource('/api/v1/heartbeat/stream');
        
        eventSource.onmessage = (event) => {
            const data = json.parse(event.data);
            setMetrics(data);
        };

        return () => eventSource.close();
    }, []);

    return (
        <div className="live-metrics-container bg-black border border-green-500/30 p-4 rounded-lg font-mono text-xs">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-green-400 uppercase tracking-widest">System Nervous System</h3>
                <div className={`h-2 w-2 rounded-full ${metrics.status === 'Resonating' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`}></div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
                <div className="metric-box">
                    <label className="text-gray-500">Resonance Score</label>
                    <div className="text-xl text-white">{(metrics.resonance_score * 100).toFixed(2)}%</div>
                </div>
                <div className="metric-box">
                    <label className="text-gray-500">Pulse (BPM)</label>
                    <div className="text-xl text-white">{metrics.system_pulse_bpm}</div>
                </div>
                <div className="metric-box">
                    <label className="text-gray-500">Active Entities</label>
                    <div className="text-xl text-white">{metrics.active_agents}</div>
                </div>
                <div className="metric-box">
                    <label className="text-gray-500">Global State</label>
                    <div className="text-xl text-green-400">{metrics.status}</div>
                </div>
            </div>

            {/* Simulated Pulse Waveform */}
            <div className="mt-4 h-12 w-full overflow-hidden border-t border-green-500/10 relative">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-green-500/20 to-transparent animate-scan"></div>
                <svg className="w-full h-full" viewBox="0 0 400 50">
                    <path 
                        d="M 0 25 Q 50 25 100 25 T 200 25 T 300 25 T 400 25" 
                        fill="none" 
                        stroke="#10b981" 
                        strokeWidth="1"
                        className="animate-pulse"
                    />
                </svg>
            </div>
        </div>
    );
};

export default LiveMetrics;
