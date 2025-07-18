import React from 'react';
import MarkdownRenderer from './MarkdownRenderer';

const ChangelogViewer = ({ changelog }) => {
  if (!changelog || changelog.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No changelog entries found
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8">
      <h3 className="text-lg font-medium text-gray-900">Changelog</h3>
      
      <div className="space-y-6">
        {changelog.map((entry, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">{entry.title}</h4>
              <span className="text-sm text-gray-500">{entry.date}</span>
            </div>
            
            {entry.changes && entry.changes.length > 0 && (
              <div className="mb-4">
                <h5 className="font-medium text-gray-700 mb-2">Changes</h5>
                <div className="text-gray-600">
                  {entry.changes.map((change, changeIndex) => (
                    <div key={changeIndex} className="mb-2">
                      <MarkdownRenderer content={change} className="text-sm" />
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {entry.files_changed && entry.files_changed.length > 0 && (
              <div className="mb-4">
                <h5 className="font-medium text-gray-700 mb-2">Files Changed</h5>
                <div className="text-gray-600">
                  {entry.files_changed.map((file, fileIndex) => (
                    <div key={fileIndex} className="mb-2">
                      <MarkdownRenderer content={file} className="text-sm" />
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {entry.impact && (
              <div className="border-t border-gray-200 pt-4">
                <h5 className="font-medium text-gray-700 mb-2">Impact</h5>
                <div className="text-gray-600">
                  <MarkdownRenderer content={entry.impact} className="text-sm" />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChangelogViewer;