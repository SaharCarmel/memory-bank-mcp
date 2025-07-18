import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'system-ui, -apple-system, sans-serif',
  fontSize: 14,
  themeVariables: {
    primaryColor: '#3b82f6',
    primaryTextColor: '#1f2937',
    primaryBorderColor: '#d1d5db',
    lineColor: '#6b7280',
    secondaryColor: '#f3f4f6',
    tertiaryColor: '#ffffff',
  },
});

const MermaidChart = ({ chart }) => {
  const chartRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (chartRef.current) {
      setError(null);
      mermaid.render(`mermaid-${Date.now()}`, chart)
        .then((result) => {
          chartRef.current.innerHTML = result.svg;
        })
        .catch((err) => {
          console.error('Mermaid parsing error:', err);
          setError(err.message);
          chartRef.current.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="ml-3">
                  <h3 class="text-sm font-medium text-red-800">Mermaid Diagram Error</h3>
                  <div class="mt-2 text-sm text-red-700">
                    <p>Unable to render diagram. Please check the syntax.</p>
                  </div>
                </div>
              </div>
              <div class="mt-4">
                <pre class="text-xs text-gray-600 bg-gray-100 p-2 rounded overflow-x-auto">${chart}</pre>
              </div>
            </div>
          `;
        });
    }
  }, [chart]);

  return <div ref={chartRef} className="mermaid-chart my-4" />;
};

const MarkdownRenderer = ({ content, className = '' }) => {
  const components = {
    // Custom code block handler for Mermaid
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      
      if (!inline && language === 'mermaid') {
        return <MermaidChart chart={String(children).replace(/\n$/, '')} />;
      }
      
      return (
        <code
          className={`${className} ${
            inline
              ? 'bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm font-mono'
              : 'block bg-gray-100 text-gray-800 p-3 rounded-lg overflow-x-auto text-sm font-mono'
          }`}
          {...props}
        >
          {children}
        </code>
      );
    },
    
    // Custom pre handler
    pre({ children }) {
      return <div className="my-4">{children}</div>;
    },
    
    // Headings
    h1({ children }) {
      return <h1 className="text-3xl font-bold text-gray-900 mb-6 mt-8 pb-2 border-b border-gray-200">{children}</h1>;
    },
    h2({ children }) {
      return <h2 className="text-2xl font-semibold text-gray-900 mb-4 mt-6 pb-2 border-b border-gray-200">{children}</h2>;
    },
    h3({ children }) {
      return <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-5">{children}</h3>;
    },
    h4({ children }) {
      return <h4 className="text-lg font-medium text-gray-900 mb-2 mt-4">{children}</h4>;
    },
    h5({ children }) {
      return <h5 className="text-base font-medium text-gray-900 mb-2 mt-3">{children}</h5>;
    },
    h6({ children }) {
      return <h6 className="text-sm font-medium text-gray-900 mb-2 mt-3">{children}</h6>;
    },
    
    // Paragraphs
    p({ children }) {
      return <p className="text-gray-700 mb-4 leading-relaxed">{children}</p>;
    },
    
    // Lists
    ul({ children }) {
      return <ul className="list-disc list-inside mb-4 text-gray-700 space-y-1">{children}</ul>;
    },
    ol({ children }) {
      return <ol className="list-decimal list-inside mb-4 text-gray-700 space-y-1">{children}</ol>;
    },
    li({ children }) {
      return <li className="ml-4">{children}</li>;
    },
    
    // Links
    a({ href, children }) {
      return (
        <a
          href={href}
          className="text-blue-600 hover:text-blue-800 underline"
          target="_blank"
          rel="noopener noreferrer"
        >
          {children}
        </a>
      );
    },
    
    // Tables
    table({ children }) {
      return (
        <div className="overflow-x-auto mb-4">
          <table className="min-w-full divide-y divide-gray-200">{children}</table>
        </div>
      );
    },
    thead({ children }) {
      return <thead className="bg-gray-50">{children}</thead>;
    },
    tbody({ children }) {
      return <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>;
    },
    tr({ children }) {
      return <tr>{children}</tr>;
    },
    th({ children }) {
      return (
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          {children}
        </th>
      );
    },
    td({ children }) {
      return <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{children}</td>;
    },
    
    // Blockquotes
    blockquote({ children }) {
      return (
        <blockquote className="border-l-4 border-blue-500 pl-4 py-2 mb-4 bg-blue-50 text-gray-700 italic">
          {children}
        </blockquote>
      );
    },
    
    // Horizontal rule
    hr() {
      return <hr className="my-6 border-gray-200" />;
    },
    
    // Strong and emphasis
    strong({ children }) {
      return <strong className="font-semibold text-gray-900">{children}</strong>;
    },
    em({ children }) {
      return <em className="italic text-gray-700">{children}</em>;
    },
  };

  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;