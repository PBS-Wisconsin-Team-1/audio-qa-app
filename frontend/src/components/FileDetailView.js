import React from 'react';
import { generateTextSummary, downloadTextFile } from '../utils/export';
import './FileDetailView.css';

const FileDetailView = ({ file, report }) => {
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
  const overallResults = isNewFormat ? (report.overall_results || []) : [];
  const detections = isNewFormat ? (report.in_file_detections || []) : (report || []);

  const handleExport = () => {
    const summary = generateTextSummary(reportFile, reportTitle, overallResults, detections);
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
            File: {reportFile} • Processed on {file.processedDate}
          </p>
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
              <div className="file-detail-issues-list">
                {detections.map((detection, index) => (
                  <div key={index} className="file-detail-issue">
                    <div className="file-detail-issue-header">
                      <span
                        className="file-detail-issue-type"
                        style={{ 
                          backgroundColor: getIssueTypeColor(detection.type),
                          color: 'white'
                        }}
                      >
                        {detection.type}
                      </span>
                      <span className="file-detail-issue-time">
                        {detection.start_mmss}
                        {detection.end !== null && detection.end_mmss !== 'N/A' && (
                          <> - {detection.end_mmss}</>
                        )}
                      </span>
                    </div>
                    <p className="file-detail-issue-details">
                      {detection.details}
                    </p>
                    {detection.params && Object.keys(detection.params).length > 0 && (
                      <div className="file-detail-issue-params">
                        <strong>Detection Parameters:</strong>
                        <ul>
                          {Object.entries(detection.params).map(([key, value]) => {
                            // Format parameter values nicely with units where appropriate
                            let displayValue = value;
                            let unit = '';
                            
                            if (typeof value === 'boolean') {
                              displayValue = value ? 'enabled' : 'disabled';
                            } else if (typeof value === 'number') {
                              // Add units based on parameter name
                              if (key === 'min_len' || key.includes('ms') || key.includes('duration')) {
                                unit = ' ms';
                              } else if (key === 'threshold') {
                                // Keep threshold as-is (could be RMS or LUFS)
                                displayValue = Number.isInteger(value) ? value : value.toFixed(3);
                              } else if (key.includes('window') || key.includes('time')) {
                                unit = ' s';
                                displayValue = Number.isInteger(value) ? value : value.toFixed(2);
                              } else {
                                displayValue = Number.isInteger(value) ? value : value.toFixed(3);
                              }
                            }
                            
                            // Format key name for display
                            const formattedKey = key
                              .replace(/_/g, ' ')
                              .replace(/\b\w/g, l => l.toUpperCase());
                            
                            return (
                              <li key={key}>
                                <strong>{formattedKey}:</strong> {displayValue}{unit}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default FileDetailView;

