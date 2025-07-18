import React from 'react';
import MarkdownRenderer from './MarkdownRenderer';

const TaskList = ({ tasks }) => {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No tasks found
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Tasks</h3>
      
      <div className="space-y-4">
        {tasks.map((task) => (
          <div key={task.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-lg font-medium text-gray-900 mb-2">{task.title}</h4>
                {task.description && (
                  <div className="text-gray-600 mb-4">
                    <MarkdownRenderer content={task.description} className="text-sm" />
                  </div>
                )}
                <div className="flex items-center space-x-4 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                  {task.priority && (
                    <span className={`font-medium ${getPriorityColor(task.priority)}`}>
                      {task.priority} priority
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right text-sm text-gray-500 ml-4">
                <div>ID: {task.id}</div>
                {task.created_at && (
                  <div>Created: {new Date(task.created_at).toLocaleDateString()}</div>
                )}
                {task.updated_at && (
                  <div>Updated: {new Date(task.updated_at).toLocaleDateString()}</div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskList;