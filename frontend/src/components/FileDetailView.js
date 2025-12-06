import React, { useState, useRef, useEffect } from 'react';
import { generateTextSummary, downloadTextFile } from '../utils/export';
import './FileDetailView.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

const FileDetailView = ({ file, report }) => {
  // State for collapsed/expanded detection types
  const [expandedTypes, setExpandedTypes] = useState({});
  // State for currently playing audio clip
  const [playingClip, setPlayingClip] = useState(null);
  const audioRefs = useRef({});

  // Cleanup audio elements on unmount
  useEffect(() => {
    return () => {
      // Stop all playing audio and cleanup
      Object.values(audioRefs.current).forEach(audio => {
        if (audio) {
          audio.pause();
          audio.src = '';
        }
      });
      audioRefs.current = {};
    };
  }, []);

  if (!file) {
    return (
      <div className="file-detail-empty">
        <p>Select a file from the gallery to view its details</p>
      </div>
    );
  }

  // Handle both new format (object) and old format (array) for backward compatibility
  const isNewFormat = report && typeof report === 'object' && !Array.isArray(report);
  const reportTitle = isNewFormat ? report.title : null;
  const reportFile = isNewFormat ? report.file : file.name;
  const allOverallResults = isNewFormat ? (report.overall_results || []) : [];
  const detections = isNewFormat ? (report.in_file_detections || []) : (report || []);

  // Extract metadata (samplerate, channels, duration) from overallResults
  const metadataTypes = ['samplerate', 'channels', 'duration'];
  const metadata = {};
  const overallResults = allOverallResults.filter(result => {
    const type = result.type.toLowerCase();
    if (metadataTypes.includes(type)) {
      metadata[type] = result.result;
      return false; // Don't include in overallResults display
    }
    return true; // Keep in overallResults display
  });

  // Group detections by type
  const detectionsByType = detections.reduce((acc, detection) => {
    const type = detection.type;
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(detection);
    return acc;
  }, {});

  // Toggle expanded state for a detection type
  const toggleType = (type) => {
    setExpandedTypes(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  // Get clip URL for a detection
  const getClipUrl = (detection) => {
    if (!file || detection.id === undefined || detection.id === null) return null;
    const clipFilename = `${detection.type.toLowerCase()}-${detection.id}.wav`;
    return `${API_BASE_URL}/api/files/${file.id}/clips/${clipFilename}`;
  };

  // Handle play/pause for audio clip
  const handlePlayClip = (detection, event) => {
    event.stopPropagation(); // Prevent toggling the detection group
    
    const clipUrl = getClipUrl(detection);
    if (!clipUrl) return;

    const clipKey = `${detection.type}-${detection.id}`;
    
    // Stop any currently playing audio
    if (playingClip && playingClip !== clipKey) {
      const prevAudio = audioRefs.current[playingClip];
      if (prevAudio) {
        prevAudio.pause();
        prevAudio.currentTime = 0;
      }
    }

    // Get or create audio element
    let audio = audioRefs.current[clipKey];
    if (!audio) {
      audio = new Audio(clipUrl);
      audioRefs.current[clipKey] = audio;
      
      // Handle audio end
      audio.addEventListener('ended', () => {
        setPlayingClip(null);
      });
      
      // Handle errors
      audio.addEventListener('error', () => {
        console.error('Error playing audio clip:', clipUrl);
        setPlayingClip(null);
      });
    }

    if (playingClip === clipKey && !audio.paused) {
      // Pause if already playing
      audio.pause();
      setPlayingClip(null);
    } else {
      // Play the clip
      audio.play().catch(err => {
        console.error('Error playing audio:', err);
        setPlayingClip(null);
      });
      setPlayingClip(clipKey);
    }
  };

  // Check if clip exists for a detection
  const hasClip = (detection) => {
    return detection.id !== undefined && detection.id !== null;
  };

  const handleExport = () => {
    const summary = generateTextSummary(reportFile, reportTitle, overallResults, detections, metadata);
    const filename = `${reportFile.replace(/\.[^/.]+$/, '')}_report.txt`;
    downloadTextFile(summary, filename);
  };

  const getIssueTypeColor = (type) => {
    switch (type) {
      case 'Clipping':
        return '#dc3545';
      case 'Cutout':
        return '#6f42c1';
      case 'Loudness':
        return '#fd7e14';
      case 'Overall LUFS':
        return '#0d6efd';
      default:
        return '#6c757d';
    }
  };

  const hasAnyData = overallResults.length > 0 || (detections && detections.length > 0);

  return (
    <div className="file-detail">
      <div className="file-detail-header">
        <div>
          <h2 className="file-detail-title">{reportTitle || reportFile}</h2>
          <p className="file-detail-meta">
            Processed on {file.processedDate}
            {metadata.duration && (
              <> • Duration: {metadata.duration}</>
            )}
          </p>
          {(metadata.samplerate || metadata.channels) && (
            <p className="file-detail-meta-secondary">
              {metadata.samplerate && (
                <>Sample Rate: {typeof metadata.samplerate === 'number' ? metadata.samplerate.toFixed(0) : metadata.samplerate} Hz</>
              )}
              {metadata.samplerate && metadata.channels && ' • '}
              {metadata.channels && (
                <>Channels: {
                  typeof metadata.channels === 'number' 
                    ? (metadata.channels === 1 ? 'mono' : metadata.channels === 2 ? 'stereo' : `${metadata.channels} channels`)
                    : metadata.channels
                }</>
              )}
            </p>
          )}
        </div>
        <button
          className="file-detail-export-btn"
          onClick={handleExport}
          disabled={!hasAnyData}
        >
          Export Report
        </button>
      </div>

      {!hasAnyData ? (
        <div className="file-detail-no-issues">
          <div className="file-detail-success-icon">✓</div>
          <h3>No Issues Detected</h3>
          <p>This audio file passed all quality checks.</p>
        </div>
      ) : (
        <>
          {/* Overall Results Section */}
          {overallResults.length > 0 && (
            <div className="file-detail-section">
              <h3 className="file-detail-section-title">Overall Results</h3>
              <div className="file-detail-overall-results">
                {overallResults.map((result, index) => (
                  <div key={index} className="file-detail-overall-result">
                    <div className="file-detail-overall-result-header">
                      <span
                        className="file-detail-overall-result-type"
                        style={{ 
                          backgroundColor: getIssueTypeColor(result.type),
                          color: 'white'
                        }}
                      >
                        {result.type}
                      </span>
                      <span className="file-detail-overall-result-value">
                        {typeof result.result === 'number' 
                          ? result.result.toFixed(2) 
                          : result.result}
                      </span>
                    </div>
                    {result.params && Object.keys(result.params).length > 0 && (
                      <div className="file-detail-overall-result-params">
                        <strong>Parameters:</strong>
                        <ul>
                          {Object.entries(result.params).map(([key, value]) => (
                            <li key={key}>
                              {key}: {value}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* In-File Detections Section */}
          {detections && detections.length > 0 && (
            <div className="file-detail-section">
              <div className="file-detail-summary">
                <div className="file-detail-summary-item">
                  <span className="file-detail-summary-label">Total Issues:</span>
                  <span className="file-detail-summary-value">{detections.length}</span>
                </div>
                {(() => {
                  const issuesByType = detections.reduce((acc, d) => {
                    acc[d.type] = (acc[d.type] || 0) + 1;
                    return acc;
                  }, {});
                  return Object.entries(issuesByType).map(([type, count]) => (
                    <div key={type} className="file-detail-summary-item">
                      <span className="file-detail-summary-label">{type}:</span>
                      <span
                        className="file-detail-summary-value"
                        style={{ color: getIssueTypeColor(type) }}
                      >
                        {count}
                      </span>
                    </div>
                  ));
                })()}
              </div>

              <h3 className="file-detail-issues-title">Detected Issues</h3>
              <div className="file-detail-detection-groups">
                {Object.entries(detectionsByType).map(([type, typeDetections]) => {
                  const isExpanded = expandedTypes[type] !== false; // Default to expanded
                  const firstDetection = typeDetections[0];
                  const params = firstDetection.params || {};
                  
                  // Get common details text (same for all instances of this type)
                  // Filter out unwanted messages
                  let commonDetails = null;
                  if (firstDetection.details) {
                    let detailsText = firstDetection.details;
                    // Remove ClipDaT algorithm message for Clipping
                    if (type === 'Clipping') {
                      detailsText = detailsText.replace(/Detected using clipdetect library's ClipDaT algorithm implementation/gi, '');
                      detailsText = detailsText.replace(/Clipping detected by ClipDaT algorithm/gi, '');
                      detailsText = detailsText.replace(/Clipping detected/gi, '').trim();
                      // If empty after filtering, don't show details
                      if (!detailsText || detailsText.length === 0) {
                        detailsText = null;
                      }
                    }
                    // Only show details if they're the same across all instances
                    const allSameDetails = typeDetections.every(d => {
                      let dDetails = d.details || '';
                      if (type === 'Clipping') {
                        dDetails = dDetails.replace(/Detected using clipdetect library's ClipDaT algorithm implementation/gi, '');
                        dDetails = dDetails.replace(/Clipping detected by ClipDaT algorithm/gi, '');
                        dDetails = dDetails.replace(/Clipping detected/gi, '').trim();
                      }
                      return dDetails === detailsText;
                    });
                    if (allSameDetails && detailsText) {
                      commonDetails = detailsText;
                    }
                  }
                  
                  // Format parameter helper function
                  const formatParameter = (key, value) => {
                    let displayValue = value;
                    let unit = '';
                    
                    if (typeof value === 'boolean') {
                      displayValue = value ? 'enabled' : 'disabled';
                    } else if (typeof value === 'number') {
                      if (key === 'min_len' || key.includes('ms') || key.includes('duration')) {
                        unit = ' ms';
                      } else if (key === 'threshold') {
                        displayValue = Number.isInteger(value) ? value : value.toFixed(3);
                      } else if (key.includes('window') || key.includes('time')) {
                        unit = ' s';
                        displayValue = Number.isInteger(value) ? value : value.toFixed(2);
                      } else {
                        displayValue = Number.isInteger(value) ? value : value.toFixed(3);
                      }
                    }
                    
                    const formattedKey = key
                      .replace(/_/g, ' ')
                      .replace(/\b\w/g, l => l.toUpperCase());
                    
                    return { formattedKey, displayValue, unit };
                  };

                  return (
                    <div key={type} className="file-detail-detection-group">
                      <div 
                        className="file-detail-detection-group-header"
                        onClick={() => toggleType(type)}
                      >
                        <div className="file-detail-detection-group-title">
                          <span className="file-detail-detection-group-icon">
                            {isExpanded ? '▼' : '▶'}
                          </span>
                          <span
                            className="file-detail-detection-group-type"
                            style={{ 
                              backgroundColor: getIssueTypeColor(type),
                              color: 'white'
                            }}
                          >
                            {type}
                          </span>
                          <span className="file-detail-detection-group-count">
                            ({typeDetections.length} {typeDetections.length === 1 ? 'detection' : 'detections'})
                          </span>
                        </div>
                      </div>
                      
                      {isExpanded && (
                        <div className="file-detail-detection-group-content">
                          {/* Common details shown once at the top */}
                          {commonDetails && (
                            <div className="file-detail-detection-group-details">
                              <strong>Description:</strong>
                              <p>{commonDetails}</p>
                            </div>
                          )}
                          
                          {/* Parameters shown once at the top */}
                          {Object.keys(params).length > 0 && (
                            <div className="file-detail-detection-group-params">
                              <strong>Detection Parameters:</strong>
                              <ul>
                                {Object.entries(params).map(([key, value]) => {
                                  const { formattedKey, displayValue, unit } = formatParameter(key, value);
                                  return (
                                    <li key={key}>
                                      <strong>{formattedKey}:</strong> {displayValue}{unit}
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          )}
                          
                          {/* List of all detection instances (timestamps only) */}
                          <div className="file-detail-detection-instances">
                            <strong>Detection Instances:</strong>
                            <ul className="file-detail-detection-instances-list">
                              {typeDetections.map((detection, index) => {
                                const clipKey = `${detection.type}-${detection.id}`;
                                const isPlaying = playingClip === clipKey;
                                const clipAvailable = hasClip(detection);
                                
                                return (
                                  <li key={index} className="file-detail-detection-instance">
                                    {clipAvailable && (
                                      <button
                                        className={`file-detail-play-btn ${isPlaying ? 'playing' : ''}`}
                                        onClick={(e) => handlePlayClip(detection, e)}
                                        title={isPlaying ? 'Pause audio' : 'Play audio clip'}
                                      >
                                        {isPlaying ? '⏸' : '▶'}
                                      </button>
                                    )}
                                    <span className="file-detail-detection-instance-time">
                                      {detection.start_mmss}
                                      {detection.end !== null && detection.end_mmss !== 'N/A' && (
                                        <> - {detection.end_mmss}</>
                                      )}
                                    </span>
                                  </li>
                                );
                              })}
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default FileDetailView;

