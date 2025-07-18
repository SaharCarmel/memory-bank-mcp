import React, { useState } from 'react';
import MarkdownRenderer from './MarkdownRenderer';

const FileViewer = ({ files }) => {
  const [selectedFile, setSelectedFile] = useState(null);

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="flex h-full">
      <div className="w-1/3 bg-gray-50 border-r border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-medium text-gray-900">Files</h3>
        </div>
        <div className="overflow-y-auto">
          {files.map((file) => (
            <div
              key={file.name}
              onClick={() => setSelectedFile(file)}
              className={`p-4 cursor-pointer hover:bg-gray-100 border-b border-gray-100 transition-colors ${
                selectedFile?.name === file.name ? 'bg-blue-50 border-blue-200' : ''
              }`}
            >
              <div className="font-medium text-gray-900">{file.name}</div>
              <div className="text-sm text-gray-500 mt-1">
                {formatFileSize(file.size)} · {new Date(file.last_modified).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {selectedFile ? (
          <>
            <div className="bg-white border-b border-gray-200 p-4">
              <h4 className="font-medium text-gray-900">{selectedFile.name}</h4>
              <p className="text-sm text-gray-500 mt-1">
                {formatFileSize(selectedFile.size)} · Modified {new Date(selectedFile.last_modified).toLocaleString()}
              </p>
            </div>
            <div className="flex-1 overflow-auto">
              {selectedFile.name.endsWith('.md') ? (
                <div className="p-6 bg-white">
                  <MarkdownRenderer content={selectedFile.content} />
                </div>
              ) : (
                <pre className="p-4 text-sm text-gray-800 whitespace-pre-wrap font-mono bg-gray-50 h-full">
                  {selectedFile.content}
                </pre>
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a file to view its content
          </div>
        )}
      </div>
    </div>
  );
};

export default FileViewer;