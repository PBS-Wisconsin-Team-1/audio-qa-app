import React, { useState, useEffect } from 'react';
import { getQueueStatus } from '../services/api';
import './QueueProgressBar.css';

const QueueProgressBar = () => {
  const [queueStatus, setQueueStatus] = useState({
    total: 0,
    completed: 0,
    inProgress: 0,
    queued: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchQueueStatus = async () => {
      try {
        const status = await getQueueStatus();
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
  }, []);

  if (loading) {
    return (
      <div className="queue-progress">
        <p>Loading queue status...</p>
      </div>
    );
  }

  const { total, completed, inProgress, queued } = queueStatus;
  const progressPercentage = total > 0 ? (completed / total) * 100 : 0;

  return (
    <div className="queue-progress">
      <div className="queue-progress-header">
        <h3>Queue Status</h3>
        {total > 0 && (
          <span className="queue-progress-count">
            {completed}/{total} completed
          </span>
        )}
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
            <span className="queue-status-item in-progress">
              In Progress: {inProgress}
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

