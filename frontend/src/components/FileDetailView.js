import React from 'react';
import { generateTextSummary, downloadTextFile } from '../utils/export';
import './FileDetailView.css';

const FileDetailView = ({ file, detections }) => {
  if (!file) {
    return (
      <div className="file-detail-empty">
        <p>Select a file from the gallery to view its details</p>
      </div>
    );
  }

  const handleExport = () => {
    const summary = generateTextSummary(file.name, detections);
    const filename = `${file.name.replace(/\.[^/.]+$/, '')}_report.txt`;
    downloadTextFile(summary, filename);
  };

  const getIssueTypeColor = (type) => {
    switch (type) {
      case 'Clipping':
        return '#dc3545';
      case 'Cutout':
        return '#6f42c1';
      default:
        return '#6c757d';
    }
  };

  return (
    <div className="file-detail">
      <div className="file-detail-header">
        <div>
          <h2 className="file-detail-title">{file.name}</h2>
          <p className="file-detail-meta">
            Processed on {file.processedDate}
          </p>
        </div>
        <button
          className="file-detail-export-btn"
          onClick={handleExport}
          disabled={!detections || detections.length === 0}
        >
          Export Report
        </button>
      </div>

      {!detections || detections.length === 0 ? (
        <div className="file-detail-no-issues">
          <div className="file-detail-success-icon">✓</div>
          <h3>No Issues Detected</h3>
          <p>This audio file passed all quality checks.</p>
        </div>
      ) : (
        <>
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

          <div className="file-detail-issues">
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
                  <p className="file-detail-issue-details">{detection.details}</p>
                  {detection.params && Object.keys(detection.params).length > 0 && (
                    <div className="file-detail-issue-params">
                      <strong>Parameters:</strong>
                      <ul>
                        {Object.entries(detection.params).map(([key, value]) => (
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
        </>
      )}
    </div>
  );
};

export default FileDetailView;

