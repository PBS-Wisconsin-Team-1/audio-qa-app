/**
 * Generate a text summary of all detected issues
 */
export const generateTextSummary = (fileName, detections) => {
  let summary = `Audio Quality Assurance Report\n`;
  summary += `================================\n\n`;
  summary += `File: ${fileName}\n`;
  summary += `Generated: ${new Date().toLocaleString()}\n\n`;
  
  if (!detections || detections.length === 0) {
    summary += `No issues detected. Audio quality is good.\n`;
    return summary;
  }
  
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
    summary += `   Details: ${detection.details}\n`;
    if (detection.params && Object.keys(detection.params).length > 0) {
      summary += `   Parameters: ${JSON.stringify(detection.params)}\n`;
    }
    summary += `\n`;
  });
  
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

