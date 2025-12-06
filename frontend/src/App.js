import React, { useState, useEffect } from 'react';
import Gallery from './components/Gallery';
import QueueProgressBar from './components/QueueProgressBar';
import FileUpload from './components/FileUpload';
import FileDetailView from './components/FileDetailView';
import AudioDirSelector from './components/AudioDirSelector';
import { getProcessedFiles, getDetectionReport, openCli } from './services/api';
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
    // Toggle: if clicking the same file, deselect it; otherwise select the new file
    if (selectedFile && selectedFile.id === file.id) {
      setSelectedFile(null);
    } else {
      setSelectedFile(file);
    }
  };

  const handleUploadSuccess = () => {
    // Reload files after successful upload
    loadFiles();
    setShowUpload(false);
  };

  const handleOpenCli = async () => {
    try {
      await openCli();
      alert('AUQA CLI opened in a new terminal window on the server.');
    } catch (err) {
      alert('Failed to open CLI. Make sure the API server is running.');
      console.error(err);
    }
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
        <div className="app-header-buttons">
          <button
            className="app-cli-button"
            onClick={handleOpenCli}
            title="Open AUQA CLI in terminal"
          >
            Open CLI
          </button>
          <button
            className="app-upload-toggle"
            onClick={() => setShowUpload(!showUpload)}
          >
            {showUpload ? 'Hide Upload' : 'Upload File'}
          </button>
        </div>
      </header>

      <main className="app-main">
        <div className="app-sidebar">
          <AudioDirSelector onDirChange={loadFiles} />
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
                report={detections}
              />
            </>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;

