/**
 * Generate a text summary of all detected issues
 */
export const generateTextSummary = (fileName, reportTitle, overallResults, detections) => {
  let summary = reportTitle ? `${reportTitle}\n` : `AuQA Report\n`;
  summary += `================================\n\n`;
  summary += `File: ${fileName}\n`;
  summary += `Generated: ${new Date().toLocaleString()}\n\n`;
  
  const hasOverallResults = overallResults && overallResults.length > 0;
  const hasDetections = detections && detections.length > 0;
  
  if (!hasOverallResults && !hasDetections) {
    summary += `No issues detected. Audio quality is good.\n`;
    return summary;
  }
  
  // Overall Results Section
  if (hasOverallResults) {
    summary += `Overall Results:\n`;
    summary += `----------------\n`;
    overallResults.forEach((result, index) => {
      summary += `${index + 1}. ${result.type}: `;
      summary += typeof result.result === 'number' 
        ? result.result.toFixed(2) 
        : result.result;
      summary += `\n`;
      if (result.params && Object.keys(result.params).length > 0) {
        summary += `   Parameters: ${JSON.stringify(result.params)}\n`;
      }
      summary += `\n`;
    });
  }
  
  // Detections Section
  if (hasDetections) {
    summary += `Total Issues Detected: ${detections.length}\n\n`;
    
    // Group by type
    const issuesByType = detections.reduce((acc, detection) => {
      const type = detection.type;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(detection);
      return acc;
    }, {});
    
    // Summary by type
    summary += `Summary by Issue Type:\n`;
    summary += `----------------------\n`;
    Object.entries(issuesByType).forEach(([type, issues]) => {
      summary += `  ${type}: ${issues.length} issue(s)\n`;
    });
    summary += `\n`;
    
    // Detailed list
    summary += `Detailed Issue List:\n`;
    summary += `--------------------\n\n`;
    
    detections.forEach((detection, index) => {
      summary += `${index + 1}. ${detection.type}\n`;
      summary += `   Time: ${detection.start_mmss}`;
      if (detection.end !== null && detection.end_mmss !== 'N/A') {
        summary += ` - ${detection.end_mmss}`;
      }
      summary += `\n`;
      // Clean up details - remove clipdetect library reference
      const cleanDetails = detection.details && detection.details.includes('clipdetect library')
        ? (detection.type === 'Clipping' ? 'Clipping detected' : detection.details)
        : detection.details;
      summary += `   Details: ${cleanDetails}\n`;
      if (detection.params && Object.keys(detection.params).length > 0) {
        summary += `   Parameters: ${JSON.stringify(detection.params)}\n`;
      }
      summary += `\n`;
    });
  }
  
  return summary;
};

/**
 * Download text file
 */
export const downloadTextFile = (content, filename) => {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

