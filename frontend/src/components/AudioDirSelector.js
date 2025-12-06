import React, { useState, useEffect } from 'react';
import { getAudioDir, setAudioDir, listAudioFiles } from '../services/api';
import './AudioDirSelector.css';

const AudioDirSelector = ({ onDirChange }) => {
  const [audioDir, setAudioDirState] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [fileCount, setFileCount] = useState(0);

  useEffect(() => {
    loadAudioDir();
  }, []);

  const loadAudioDir = async () => {
    try {
      setLoading(true);
      setError(null);
      const config = await getAudioDir();
      setAudioDirState(config.audio_dir || '');
      
      // Load file count
      try {
        const files = await listAudioFiles();
        setFileCount(files.count || 0);
      } catch (err) {
        console.error('Failed to list files:', err);
      }
    } catch (err) {
      setError(err.message || 'Failed to load audio directory');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!audioDir.trim()) {
      setError('Please enter a directory path');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      
      const result = await setAudioDir(audioDir.trim());
      setSuccess(result.message || 'Audio directory updated successfully');
      
      // Reload file count
      try {
        const files = await listAudioFiles();
        setFileCount(files.count || 0);
      } catch (err) {
        console.error('Failed to list files:', err);
      }
      
      if (onDirChange) {
        onDirChange(audioDir.trim());
      }
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to update audio directory');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setAudioDirState('');
    setError(null);
    setSuccess(null);
  };

  if (loading) {
    return (
      <div className="audio-dir-selector">
        <div className="audio-dir-loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="audio-dir-selector">
      <h3>Audio Files Directory</h3>
      <div className="audio-dir-input-group">
        <label htmlFor="audio-dir-input">Select folder for audio files:</label>
        <div className="audio-dir-input-wrapper">
          <input
            id="audio-dir-input"
            type="text"
            value={audioDir}
            onChange={(e) => setAudioDirState(e.target.value)}
            placeholder="/path/to/audio/files"
            className="audio-dir-input"
            disabled={saving}
          />
          <div className="audio-dir-actions">
            <button
              onClick={handleSave}
              disabled={saving || !audioDir.trim()}
              className="audio-dir-save-btn"
            >
              {saving ? 'Saving...' : 'Set Directory'}
            </button>
            <button
              onClick={handleReset}
              disabled={saving}
              className="audio-dir-reset-btn"
            >
              Reset
            </button>
          </div>
        </div>
        {fileCount > 0 && (
          <p className="audio-dir-info">
            Found {fileCount} audio file{fileCount !== 1 ? 's' : ''} in this directory
          </p>
        )}
      </div>
      {error && (
        <div className="audio-dir-error">
          {error}
        </div>
      )}
      {success && (
        <div className="audio-dir-success">
          {success}
        </div>
      )}
      <div className="audio-dir-hint">
        <p><strong>Tip:</strong> Enter the full path to the folder containing your audio files.</p>
        <p>Example: <code>/Users/username/Music</code> or <code>C:\Users\username\Music</code></p>
      </div>
    </div>
  );
};

export default AudioDirSelector;

