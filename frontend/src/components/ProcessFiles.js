import React, { useState, useEffect } from 'react';
import { listAudioFiles, uploadAudioFile, getDetectionTypes, queueJob } from '../services/api';
import './ProcessFiles.css';

const ProcessFiles = ({ onJobQueued }) => {
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState(new Set());
  const [detectionTypes, setDetectionTypes] = useState({});
  const [selectedDetectionTypes, setSelectedDetectionTypes] = useState(new Set());
  const [detectionParams, setDetectionParams] = useState({});
  const [clipPad, setClipPad] = useState(0.1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    loadAvailableFiles();
    loadDetectionTypes();
  }, []);

  const loadAvailableFiles = async () => {
    try {
      const data = await listAudioFiles();
      setAvailableFiles(data.files || []);
    } catch (err) {
      console.error('Error loading files:', err);
      setError('Failed to load audio files');
    }
  };

  const loadDetectionTypes = async () => {
    try {
      const data = await getDetectionTypes();
      setDetectionTypes(data.detection_types || {});
      // Initialize with all types selected
      setSelectedDetectionTypes(new Set(Object.keys(data.detection_types || {})));
      // Initialize default parameters
      const defaultParams = {};
      Object.entries(data.detection_types || {}).forEach(([type, config]) => {
        defaultParams[type] = { ...config.params };
      });
      setDetectionParams(defaultParams);
    } catch (err) {
      console.error('Error loading detection types:', err);
      setError('Failed to load detection types');
    }
  };

  const handleFileToggle = (fileName) => {
    setSelectedFiles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(fileName)) {
        newSet.delete(fileName);
      } else {
        newSet.add(fileName);
      }
      return newSet;
    });
  };

  const handleSelectAllFiles = () => {
    if (selectedFiles.size === availableFiles.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(availableFiles.map(f => f.name)));
    }
  };

  const handleDetectionTypeToggle = (detType) => {
    setSelectedDetectionTypes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(detType)) {
        newSet.delete(detType);
      } else {
        newSet.add(detType);
        // Initialize parameters if not already set
        if (!detectionParams[detType] && detectionTypes[detType]) {
          setDetectionParams(prevParams => ({
            ...prevParams,
            [detType]: { ...detectionTypes[detType].params }
          }));
        }
      }
      return newSet;
    });
  };

  const handleSelectAllDetectionTypes = () => {
    const allTypes = Object.keys(detectionTypes);
    if (selectedDetectionTypes.size === allTypes.length) {
      setSelectedDetectionTypes(new Set());
    } else {
      setSelectedDetectionTypes(new Set(allTypes));
      // Initialize parameters for all types
      const defaultParams = {};
      allTypes.forEach(type => {
        defaultParams[type] = { ...detectionTypes[type].params };
      });
      setDetectionParams(prev => ({ ...prev, ...defaultParams }));
    }
  };

  const handleParamChange = (detType, paramName, value) => {
    setDetectionParams(prev => ({
      ...prev,
      [detType]: {
        ...prev[detType],
        [paramName]: value === '' ? undefined : (isNaN(value) ? value : parseFloat(value))
      }
    }));
  };

  const handleFileUpload = async (file) => {
    setUploading(true);
    setError(null);
    try {
      await uploadAudioFile(file);
      // Reload available files
      await loadAvailableFiles();
      // Auto-select the uploaded file
      setSelectedFiles(prev => new Set([...prev, file.name]));
    } catch (err) {
      setError(err.message || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const audioFiles = files.filter(file => 
      file.type.startsWith('audio/') || 
      /\.(wav|mp3|flac|ogg|m4a)$/i.test(file.name)
    );
    
    if (audioFiles.length > 0) {
      for (const file of audioFiles) {
        await handleFileUpload(file);
      }
    } else {
      setError('Please drop audio files (WAV, MP3, FLAC, etc.)');
    }
  };

  const handleQueueJob = async () => {
    if (selectedFiles.size === 0) {
      setError('Please select at least one file');
      return;
    }

    if (selectedDetectionTypes.size === 0) {
      setError('Please select at least one detection type');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Build detection params object with only selected types
      const paramsToQueue = {};
      selectedDetectionTypes.forEach(detType => {
        // Only include non-empty parameters
        const params = {};
        if (detectionParams[detType]) {
          Object.entries(detectionParams[detType]).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
              params[key] = value;
            }
          });
        }
        paramsToQueue[detType] = params;
      });

      const result = await queueJob(
        Array.from(selectedFiles),
        paramsToQueue,
        clipPad
      );

      setSuccess(`Successfully queued ${result.queued.length} file(s) for processing`);
      
      if (result.errors && result.errors.length > 0) {
        console.warn('Some files had errors:', result.errors);
      }

      // Clear selection
      setSelectedFiles(new Set());
      
      if (onJobQueued) {
        onJobQueued();
      }

      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      setError(err.message || 'Failed to queue job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="process-files">
      <h3>Process Audio Files</h3>
      
      {/* File Selection Section */}
      <div className="process-files-section">
        <div className="process-files-section-header">
          <h4>Select Files</h4>
          <button
            className="process-files-select-all-btn"
            onClick={handleSelectAllFiles}
          >
            {selectedFiles.size === availableFiles.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>
        
        {/* Upload Area */}
        <div
          className={`process-files-upload-area ${uploading ? 'uploading' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <div className="process-files-upload-icon">📤</div>
          <p>Drag and drop files here or click to browse</p>
          <input
            type="file"
            accept="audio/*,.wav,.mp3,.flac,.ogg,.m4a"
            onChange={(e) => {
              const files = Array.from(e.target.files);
              files.forEach(file => handleFileUpload(file));
              e.target.value = '';
            }}
            className="process-files-upload-input"
            disabled={uploading}
            multiple
          />
        </div>

        {/* Available Files List */}
        <div className="process-files-file-list">
          {availableFiles.length === 0 ? (
            <p className="process-files-empty">No audio files found in directory</p>
          ) : (
            availableFiles.map((file) => (
              <label key={file.name} className="process-files-file-item">
                <input
                  type="checkbox"
                  checked={selectedFiles.has(file.name)}
                  onChange={() => handleFileToggle(file.name)}
                />
                <span className="process-files-file-name">{file.name}</span>
                <span className="process-files-file-size">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </span>
              </label>
            ))
          )}
        </div>
        {selectedFiles.size > 0 && (
          <p className="process-files-selected-count">
            {selectedFiles.size} file(s) selected
          </p>
        )}
      </div>

      {/* Detection Types Section */}
      <div className="process-files-section">
        <div className="process-files-section-header">
          <h4>Detection Types</h4>
          <button
            className="process-files-select-all-btn"
            onClick={handleSelectAllDetectionTypes}
          >
            {selectedDetectionTypes.size === Object.keys(detectionTypes).length ? 'Deselect All' : 'Select All'}
          </button>
        </div>
        <div className="process-files-detection-types">
          {Object.entries(detectionTypes).map(([detType, config]) => (
            <div key={detType} className="process-files-detection-type">
              <label className="process-files-detection-type-label">
                <input
                  type="checkbox"
                  checked={selectedDetectionTypes.has(detType)}
                  onChange={() => handleDetectionTypeToggle(detType)}
                />
                <span>{detType}</span>
                <span className="process-files-detection-type-badge">
                  {config.type}
                </span>
              </label>
              
              {/* Parameters for this detection type */}
              {selectedDetectionTypes.has(detType) && 
               config.params && 
               Object.keys(config.params).length > 0 && (
                <div className="process-files-params">
                  {Object.entries(config.params).map(([paramName, defaultValue]) => (
                    <div key={paramName} className="process-files-param">
                      <label>
                        {paramName.replace(/_/g, ' ')}:
                        <input
                          type="number"
                          step="any"
                          placeholder={defaultValue}
                          value={detectionParams[detType]?.[paramName] ?? ''}
                          onChange={(e) => handleParamChange(detType, paramName, e.target.value)}
                        />
                        <span className="process-files-param-default">
                          (default: {defaultValue})
                        </span>
                      </label>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Advanced Options */}
      <div className="process-files-section">
        <button
          className="process-files-advanced-toggle"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? '▼' : '▶'} Advanced Options
        </button>
        {showAdvanced && (
          <div className="process-files-advanced">
            <label>
              Clip Padding (seconds):
              <input
                type="number"
                step="0.1"
                min="0"
                value={clipPad}
                onChange={(e) => setClipPad(parseFloat(e.target.value) || 0.1)}
              />
            </label>
          </div>
        )}
      </div>

      {/* Queue Button */}
      <button
        className="process-files-queue-btn"
        onClick={handleQueueJob}
        disabled={loading || selectedFiles.size === 0 || selectedDetectionTypes.size === 0}
      >
        {loading ? 'Queueing...' : `Queue ${selectedFiles.size} File(s) for Processing`}
      </button>

      {/* Messages */}
      {error && (
        <div className="process-files-error">
          {error}
        </div>
      )}
      {success && (
        <div className="process-files-success">
          {success}
        </div>
      )}
    </div>
  );
};

export default ProcessFiles;

