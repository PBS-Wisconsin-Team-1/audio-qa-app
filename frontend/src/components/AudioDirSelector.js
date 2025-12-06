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

  const handleBrowseDirectory = async () => {
    // Check if File System Access API is supported (Chrome, Edge, Opera)
    if ('showDirectoryPicker' in window) {
      try {
        const directoryHandle = await window.showDirectoryPicker();
        const dirName = directoryHandle.name;
        
        // Try to get the full path using the handle's getDirectoryHandle or by reading files
        // Unfortunately, browsers don't expose the full absolute path for security reasons
        // We'll try to construct a helpful message and guide the user
        
        // Try to get a file from the directory to extract path info
        try {
          // Get the first entry to try to extract path information
          const entries = [];
          for await (const entry of directoryHandle.values()) {
            entries.push(entry);
            break; // Just get the first one
          }
          
          if (entries.length > 0) {
            const firstEntry = entries[0];
            // Try to get the path - this may not work in all cases
            // The browser security model prevents direct path access
            setSuccess(`Selected directory: "${dirName}". Please copy the full path from your file explorer and paste it above.`);
            setError(null);
          } else {
            setSuccess(`Selected directory: "${dirName}". Please copy the full path from your file explorer and paste it above.`);
            setError(null);
          }
        } catch (err) {
          setSuccess(`Selected directory: "${dirName}". Please copy the full path from your file explorer and paste it below.`);
          setError(null);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Error selecting directory:', err);
          setError('Failed to select directory. Please enter the path manually.');
        }
        // User cancelled - don't show error
      }
    } else {
      // Fallback: use the traditional file input with webkitdirectory
      // This works in Firefox and other browsers
      const input = document.createElement('input');
      input.type = 'file';
      input.webkitdirectory = true;
      input.directory = true;
      input.multiple = true;
      
      input.onchange = (e) => {
        const files = e.target.files;
        if (files.length > 0) {
          const firstFile = files[0];
          // Extract directory name from webkitRelativePath
          const relativePath = firstFile.webkitRelativePath || firstFile.name;
          const dirName = relativePath.includes('/') ? relativePath.split('/')[0] : 'selected directory';
          
          setSuccess(`Selected directory: "${dirName}". Please copy the full path from your file explorer and paste it below.`);
          setError(null);
        }
      };
      
      input.oncancel = () => {
        // User cancelled - do nothing
      };
      
      input.click();
    }
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
          <button
            onClick={handleBrowseDirectory}
            disabled={saving}
            className="audio-dir-browse-btn"
            type="button"
          >
            Browse
          </button>
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

