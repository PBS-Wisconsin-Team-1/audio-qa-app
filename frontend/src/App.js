import React, { useState, useEffect, useRef } from 'react';
import Gallery from './components/Gallery';
import QueueProgressBar from './components/QueueProgressBar';
import ProcessFiles from './components/ProcessFiles';
import FileDetailView from './components/FileDetailView';
import AudioDirSelector from './components/AudioDirSelector';
import { getProcessedFiles, getDetectionReport, deleteFiles, getBulkReports, openCli, getQueueStatus } from './services/api';
import { generateTextSummary, downloadTextFile } from './utils/export';
import './App.css';

const SESSION_STORAGE_KEY = 'auqa_queue_session_start';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [detections, setDetections] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasActiveJobs, setHasActiveJobs] = useState(false);
  const sessionStartTimeRef = useRef(null);

  // Initialize session start time
  useEffect(() => {
    let sessionStart = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!sessionStart) {
      sessionStart = Math.floor(Date.now() / 1000);
      sessionStorage.setItem(SESSION_STORAGE_KEY, sessionStart.toString());
    }
    sessionStartTimeRef.current = parseInt(sessionStart, 10);
  }, []);

  // Monitor queue status to determine polling frequency
  useEffect(() => {
    if (sessionStartTimeRef.current === null) return;

    const checkQueueStatus = async () => {
      try {
        const status = await getQueueStatus(sessionStartTimeRef.current);
        const hasJobs = (status.inProgress > 0 || status.queued > 0);
        setHasActiveJobs(hasJobs);
      } catch (error) {
        console.error('Failed to check queue status:', error);
      }
    };

    checkQueueStatus();
    const interval = setInterval(checkQueueStatus, 2000);
    return () => clearInterval(interval);
  }, []);

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

  // Auto-refresh files list when jobs are active
  useEffect(() => {
    if (sessionStartTimeRef.current === null) return;

    // Poll more frequently when jobs are active, less when idle
    const pollInterval = hasActiveJobs ? 3000 : 10000; // 3s when active, 10s when idle

    const pollForNewFiles = async () => {
      try {
        const processedFiles = await getProcessedFiles();
        // Only update if the number of files changed (new files added)
        setFiles(prevFiles => {
          // Check if we have new files by comparing counts or IDs
          if (processedFiles.length !== prevFiles.length) {
            return processedFiles;
          }
          // Check if any file IDs are new
          const prevIds = new Set(prevFiles.map(f => f.id));
          const hasNewFiles = processedFiles.some(f => !prevIds.has(f.id));
          
          // If we have a selected file, check if it was updated
          if (selectedFile && hasNewFiles) {
            const updatedFile = processedFiles.find(f => f.id === selectedFile.id);
            if (updatedFile && updatedFile.processedDate !== selectedFile.processedDate) {
              // File was updated, reload its detections
              setTimeout(() => loadDetections(selectedFile.id), 500);
            }
          }
          
          return hasNewFiles ? processedFiles : prevFiles;
        });
      } catch (err) {
        // Silently fail during polling to avoid spamming errors
        console.error('Error polling for new files:', err);
      }
    };

    const interval = setInterval(pollForNewFiles, pollInterval);
    return () => clearInterval(interval);
  }, [hasActiveJobs, selectedFile]);

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


  const handleJobQueued = () => {
    // Reload files after job is queued
    loadFiles();
  };

  const handleFilesDeleted = async (fileIds) => {
    try {
      await deleteFiles(fileIds);
      // Reload files list
      await loadFiles();
      // Clear selection if deleted file was selected
      if (selectedFile && fileIds.includes(selectedFile.id)) {
        setSelectedFile(null);
        setDetections(null);
      }
    } catch (error) {
      console.error('Error deleting files:', error);
      throw error; // Re-throw to let Gallery handle the error message
    }
  };

  const handleBulkExport = async (fileIds) => {
    try {
      const { reports, errors } = await getBulkReports(fileIds);
      
      if (errors && errors.length > 0) {
        console.warn('Some files could not be exported:', errors);
      }
      
      if (reports.length === 0) {
        alert('No reports could be exported.');
        return;
      }
      
      // Export each report as an individual file
      reports.forEach((item, index) => {
        const { report } = item;
        const isNewFormat = report && typeof report === 'object' && !Array.isArray(report);
        const reportTitle = isNewFormat ? report.title : null;
        const reportFile = isNewFormat ? report.file : `File ${index + 1}`;
        const overallResults = isNewFormat ? (report.overall_results || []) : [];
        const detections = isNewFormat ? (report.in_file_detections || []) : (report || []);
        
        // Extract metadata
        const metadataTypes = ['samplerate', 'channels', 'duration'];
        const metadata = {};
        const filteredOverallResults = overallResults.filter(result => {
          const type = result.type.toLowerCase();
          if (metadataTypes.includes(type)) {
            metadata[type] = result.result;
            return false;
          }
          return true;
        });
        
        // Generate individual report summary
        const fileSummary = generateTextSummary(reportFile, reportTitle, filteredOverallResults, detections, metadata);
        
        // Create filename from report file name
        const filename = `${reportFile.replace(/\.[^/.]+$/, '')}_report.txt`;
        
        // Add a small delay between downloads to avoid browser blocking multiple downloads
        setTimeout(() => {
          downloadTextFile(fileSummary, filename);
        }, index * 200); // 200ms delay between each download
      });
      
      // Show success message
      if (reports.length > 0) {
        alert(`Successfully exported ${reports.length} report(s). Check your downloads folder.`);
      }
    } catch (error) {
      console.error('Error exporting files:', error);
      throw error; // Re-throw to let Gallery handle the error message
    }
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
        </div>
      </header>

      <main className="app-main">
        <div className="app-sidebar">
          <QueueProgressBar />
          <ProcessFiles onJobQueued={handleJobQueued} />
          <AudioDirSelector onDirChange={loadFiles} />
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
                onFilesDeleted={handleFilesDeleted}
                onBulkExport={handleBulkExport}
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

