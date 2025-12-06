import React, { useState, useEffect, useRef } from 'react';
import './Gallery.css';

const ROWS_PER_PAGE = 2;

const Gallery = ({ files, onFileSelect, selectedFileId }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(8);
  const gridRef = useRef(null);

  // Reset to page 1 when files change
  useEffect(() => {
    setCurrentPage(1);
  }, [files]);

  // Calculate items per page based on grid width
  useEffect(() => {
    const calculateItemsPerPage = () => {
      if (!gridRef.current) return;
      
      const grid = gridRef.current;
      const gridWidth = grid.offsetWidth;
      const gap = 20; // gap between items
      const minItemWidth = 250; // minmax(250px, 1fr) from CSS
      
      // Calculate how many columns fit
      // We need to account for gaps: (n-1) * gap
      // gridWidth = n * itemWidth + (n-1) * gap
      // For minimum width: gridWidth >= n * minItemWidth + (n-1) * gap
      // Solving: n <= (gridWidth + gap) / (minItemWidth + gap)
      const columns = Math.floor((gridWidth + gap) / (minItemWidth + gap));
      const cols = Math.max(1, columns); // At least 1 column
      
      // Items per page = rows * columns
      const items = ROWS_PER_PAGE * cols;
      setItemsPerPage(items);
    };

    // Initial calculation with a small delay to ensure DOM is ready
    const timeoutId = setTimeout(calculateItemsPerPage, 100);
    
    // Recalculate on window resize
    let resizeObserver;
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        calculateItemsPerPage();
      });
      
      if (gridRef.current) {
        resizeObserver.observe(gridRef.current);
      }
    }
    
    window.addEventListener('resize', calculateItemsPerPage);
    
    return () => {
      clearTimeout(timeoutId);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      window.removeEventListener('resize', calculateItemsPerPage);
    };
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
  const totalPages = Math.ceil(files.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
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
      <div className="gallery-grid" ref={gridRef}>
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

