import React from 'react';
import './Gallery.css';

const Gallery = ({ files, onFileSelect, selectedFileId }) => {
  if (!files || files.length === 0) {
    return (
      <div className="gallery-empty">
        <p>No processed files found.</p>
        <p className="gallery-empty-hint">Upload and process audio files to see them here.</p>
      </div>
    );
  }

  return (
    <div className="gallery">
      <h2 className="gallery-title">Processed Files</h2>
      <div className="gallery-grid">
        {files.map((file) => (
          <div
            key={file.id}
            className={`gallery-item ${selectedFileId === file.id ? 'selected' : ''}`}
            onClick={() => onFileSelect(file)}
          >
            <div className="gallery-item-icon">🎵</div>
            <div className="gallery-item-info">
              <h3 className="gallery-item-name">{file.name}</h3>
              <p className="gallery-item-meta">
                {file.issueCount} issue{file.issueCount !== 1 ? 's' : ''} detected
              </p>
              <p className="gallery-item-date">{file.processedDate}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Gallery;

