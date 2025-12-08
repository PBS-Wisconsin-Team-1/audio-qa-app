import React, { useState, useEffect } from 'react';
import { getQueueStatus } from '../services/api';
import './QueueProgressBar.css';

const SESSION_STORAGE_KEY = 'auqa_queue_session_start';

const QueueProgressBar = () => {
  const [queueStatus, setQueueStatus] = useState({
    total: 0,
    completed: 0,
    inProgress: 0,
    queued: 0,
  });
  const [loading, setLoading] = useState(true);
  const [sessionStartTime, setSessionStartTime] = useState(null);

  // Initialize session start time on mount
  useEffect(() => {
    // Get or create session start timestamp
    let sessionStart = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!sessionStart) {
      // New session - store current timestamp
      sessionStart = Math.floor(Date.now() / 1000); // Unix timestamp in seconds
      sessionStorage.setItem(SESSION_STORAGE_KEY, sessionStart.toString());
    }
    setSessionStartTime(parseInt(sessionStart, 10));
  }, []);

  useEffect(() => {
    if (sessionStartTime === null) return; // Wait for session start time to be set

    const fetchQueueStatus = async () => {
      try {
        // Pass session start timestamp to only get jobs from this session
        const status = await getQueueStatus(sessionStartTime);
        setQueueStatus(status);
      } catch (error) {
        console.error('Failed to fetch queue status:', error);
        // Set default empty state on error
        setQueueStatus({ total: 0, completed: 0, inProgress: 0, queued: 0 });
      } finally {
        setLoading(false);
      }
    };

    fetchQueueStatus();
    // Poll every 2 seconds
    const interval = setInterval(fetchQueueStatus, 2000);

    return () => clearInterval(interval);
  }, [sessionStartTime]);

  if (loading) {
    return (
      <div className="queue-progress">
        <p>Loading queue status...</p>
      </div>
    );
  }

  const { total, completed, inProgress, queued } = queueStatus;
  const progressPercentage = total > 0 ? (completed / total) * 100 : 0;

  const handleReset = () => {
    // Reset session start time to now
    const newSessionStart = Math.floor(Date.now() / 1000);
    sessionStorage.setItem(SESSION_STORAGE_KEY, newSessionStart.toString());
    setSessionStartTime(newSessionStart);
    // Reset status immediately
    setQueueStatus({ total: 0, completed: 0, inProgress: 0, queued: 0 });
  };

  return (
    <div className="queue-progress">
      <div className="queue-progress-header">
        <h3>Queue Status</h3>
        <div className="queue-progress-header-right">
          {total > 0 && (
            <span className="queue-progress-count">
              {completed}/{total} completed
            </span>
          )}
          <button 
            className="queue-reset-btn" 
            onClick={handleReset}
            title="Clear queue counter (starts fresh from now)"
          >
            Clear Queue
          </button>
        </div>
      </div>
      
      {total > 0 ? (
        <>
          <div className="queue-progress-bar-container">
            <div
              className="queue-progress-bar"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="queue-progress-details">
            <span className="queue-status-item queued">
              Queued: {queued}
            </span>
            <span className="queue-status-item completed">
              Completed: {completed}
            </span>
          </div>
        </>
      ) : (
        <p className="queue-progress-empty">No jobs in queue</p>
      )}
    </div>
  );
};

export default QueueProgressBar;

