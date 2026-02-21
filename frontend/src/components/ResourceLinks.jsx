import React from 'react';

export function ResourceLinks({ resources }) {
  if (!resources || resources.length === 0) {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4">Recommended Resources</h3>
        <p className="text-gray-500">No resources found</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-xl font-bold mb-4">Recommended Resources</h3>
      
      <div className="space-y-3">
        {resources.map((resource, index) => (
          <div key={index} className="p-4 bg-gray-50 rounded border border-gray-200 hover:border-blue-300 transition">
            <h4 className="font-semibold text-gray-900 mb-1">
              {resource.name}
            </h4>
            <p className="text-sm text-gray-600 mb-3">
              {resource.description}
            </p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">
                Relevance: {(resource.relevance * 100).toFixed(0)}%
              </span>
              <a
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Visit →
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
