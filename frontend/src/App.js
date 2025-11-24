import React, { useState, useEffect } from 'react';
import Gallery from './components/Gallery';
import QueueProgressBar from './components/QueueProgressBar';
import FileUpload from './components/FileUpload';
import FileDetailView from './components/FileDetailView';
import { getProcessedFiles, getDetectionReport } from './services/api';
import './App.css';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [detections, setDetections] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    loadFiles();
  }, []);

  useEffect(() => {
    if (selectedFile) {
      loadDetections(selectedFile.id);
    } else {
      setDetections(null);
    }
  }, [selectedFile]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const processedFiles = await getProcessedFiles();
      setFiles(processedFiles);
    } catch (err) {
      setError('Failed to load processed files. Make sure the API server is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadDetections = async (fileId) => {
    try {
      setDetections(null);
      const report = await getDetectionReport(fileId);
      setDetections(report);
    } catch (err) {
      console.error('Failed to load detection report:', err);
      setDetections([]);
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
  };

  const handleUploadSuccess = () => {
    // Reload files after successful upload
    loadFiles();
    setShowUpload(false);
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="app-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-titles">
          <h1>
            <img src="/icons/favicon.svg" alt="AuQA Logo" className="app-logo" />
            <strong>AuQA</strong>
          </h1>
          <h2>Audio Quality Assurance Application</h2>
        </div>
        <button
          className="app-upload-toggle"
          onClick={() => setShowUpload(!showUpload)}
        >
          {showUpload ? 'Hide Upload' : 'Upload File'}
        </button>
      </header>

      <main className="app-main">
        <div className="app-sidebar">
          <QueueProgressBar />
          {showUpload && (
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          )}
        </div>

        <div className="app-content">
          {error ? (
            <div className="app-error">
              <p>{error}</p>
              <button onClick={loadFiles}>Retry</button>
            </div>
          ) : (
            <>
              <Gallery
                files={files}
                onFileSelect={handleFileSelect}
                selectedFileId={selectedFile?.id}
              />
              <FileDetailView
                file={selectedFile}
                detections={detections}
              />
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;

