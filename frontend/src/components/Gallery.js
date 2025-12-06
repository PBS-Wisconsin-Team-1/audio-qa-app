import React, { useState, useEffect } from 'react';
import './Gallery.css';

const ITEMS_PER_PAGE = 6;

const Gallery = ({ files, onFileSelect, selectedFileId }) => {
  const [currentPage, setCurrentPage] = useState(1);

  // Reset to page 1 when files change
  useEffect(() => {
    setCurrentPage(1);
  }, [files]);

  if (!files || files.length === 0) {
    return (
      <div className="gallery-empty">
        <p>No processed files found.</p>
        <p className="gallery-empty-hint">Upload and process audio files to see them here.</p>
      </div>
    );
  }

  // Calculate pagination
  const totalPages = Math.ceil(files.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentFiles = files.slice(startIndex, endIndex);

  const handlePrevious = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePageClick = (page) => {
    setCurrentPage(page);
  };

  return (
    <div className="gallery">
      <div className="gallery-header">
        <h2 className="gallery-title">Processed Files</h2>
        {totalPages > 1 && (
          <p className="gallery-page-info">
            Page {currentPage} of {totalPages} ({files.length} total)
          </p>
        )}
      </div>
      <div className="gallery-grid">
        {currentFiles.map((file) => (
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
      
      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="gallery-pagination">
          <button
            className="gallery-pagination-btn"
            onClick={handlePrevious}
            disabled={currentPage === 1}
          >
            ← Previous
          </button>
          
          <div className="gallery-pagination-pages">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
              // Show first page, last page, current page, and pages around current
              if (
                page === 1 ||
                page === totalPages ||
                (page >= currentPage - 1 && page <= currentPage + 1)
              ) {
                return (
                  <button
                    key={page}
                    className={`gallery-pagination-page ${
                      page === currentPage ? 'active' : ''
                    }`}
                    onClick={() => handlePageClick(page)}
                  >
                    {page}
                  </button>
                );
              } else if (
                page === currentPage - 2 ||
                page === currentPage + 2
              ) {
                return <span key={page} className="gallery-pagination-ellipsis">...</span>;
              }
              return null;
            })}
          </div>
          
          <button
            className="gallery-pagination-btn"
            onClick={handleNext}
            disabled={currentPage === totalPages}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

export default Gallery;

