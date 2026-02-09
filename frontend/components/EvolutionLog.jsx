import React, { useState, useEffect } from 'react';

const EvolutionLog = () => {
    const [events, setEvents] = useState([]);

    useEffect(() => {
        // Fetch historical log events
        const fetchLogs = async () => {
            try {
                const response = await fetch('/api/v1/logs/evolution');
                const data = await response.json();
                setEvents(data.event_log || []);
            } catch (error) {
                console.error("Error fetching evolution logs:", error);
            }
        };

        fetchLogs();
    }, []);

    return (
        <div className="evolution-log-container bg-black/80 p-6 rounded-lg border border-white/10 font-mono">
            <h2 className="text-white text-lg mb-4 flex items-center gap-2">
                <span>🦅</span> Evolution Log
            </h2>
            <div className="space-y-4">
                {events.map((event, index) => (
                    <div key={index} className="event-card border-l-2 border-green-500 pl-4 py-2 bg-white/5">
                        <div className="flex justify-between text-[10px] text-gray-500 mb-1">
                            <span>{new Date(event.timestamp).toLocaleString()}</span>
                            <span className="uppercase text-green-500/50">{event.decision_type}</span>
                        </div>
                        <div className="text-sm text-gray-200 mb-2">
                            {event.action_taken}
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(event.reasoning_weights).map(([key, weight]) => (
                                <div key={key} className="flex items-center gap-1 text-[9px] bg-black px-2 py-0.5 rounded border border-white/5">
                                    <span className="text-gray-500">{key}</span>
                                    <span className="text-white">{(weight * 100).toFixed(0)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default EvolutionLog;
