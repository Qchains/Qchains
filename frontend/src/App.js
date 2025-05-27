import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [sessionId, setSessionId] = useState('');
  const [strictMode, setStrictMode] = useState(false);
  const [llmInput, setLlmInput] = useState('');
  const [results, setResults] = useState([]);
  const [currentCollector, setCurrentCollector] = useState(null);
  const [memoryTrail, setMemoryTrail] = useState([]);
  const [activeSessions, setActiveSessions] = useState([]);
  const [iterationState, setIterationState] = useState(null);
  const [rewindResults, setRewindResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const resultRef = useRef(null);

  // Sample LLM responses for demonstration
  const sampleResponses = [
    {
      name: "ChatGPT-style Response",
      content: `I'll help you with that task. Here's the analysis:

{
  "task": "user_authentication",
  "priority": "high",
  "steps": ["validate_credentials", "create_session", "log_activity"]
}

// This is a comment about the progress
The next step would be implementation. Here's the configuration:

{
  "config": {
    "timeout": 3600,
    "retry_attempts": 3,
    "security_level": "enhanced"
  },
  "metadata": {
    "created_by": "assistant",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}

/* Multi-line comment
   explaining the security considerations
   and implementation details */`
    },
    {
      name: "Code Generation Response",
      content: `Here's the generated code structure:

{
  "components": ["AuthProvider", "LoginForm", "Dashboard"],
  "dependencies": {
    "react": "^18.0.0",
    "axios": "^1.6.0"
  }
}

// Configuration for the build process
And the build configuration:

{
  "build": {
    "target": "production",
    "optimize": true,
    "bundle_size": "minimized"
  }
}`
    },
    {
      name: "Data Analysis Response",
      content: `Based on the dataset analysis:

{
  "findings": {
    "total_records": 15420,
    "accuracy": 0.94,
    "confidence_interval": [0.91, 0.97]
  },
  "recommendations": [
    "increase_sample_size",
    "validate_outliers",
    "cross_reference_sources"
  ]
}

// Statistical significance note
The results show statistical significance with p < 0.05.

{
  "statistics": {
    "p_value": 0.032,
    "effect_size": 0.78,
    "power": 0.85
  }
}`
    }
  ];

  useEffect(() => {
    loadActiveSessions();
  }, []);

  const loadActiveSessions = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/sessions`);
      const data = await response.json();
      setActiveSessions(data.active_sessions || []);
    } catch (err) {
      console.error('Error loading sessions:', err);
    }
  };

  const createCollector = async () => {
    if (!sessionId.trim()) {
      setError('Please enter a session ID');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          strict_mode: strictMode
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentCollector(data);
        loadCollectorStatus();
        loadActiveSessions();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create collector');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const processLLMResponse = async () => {
    if (!llmInput.trim()) {
      setError('Please enter some LLM response content');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: llmInput,
          session_id: sessionId || 'default',
          strict_mode: strictMode
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResults(prev => [...prev, {
          id: Date.now(),
          input: llmInput.substring(0, 100) + (llmInput.length > 100 ? '...' : ''),
          extracted: data.extracted_json,
          status: data.status,
          timestamp: new Date().toLocaleTimeString()
        }]);
        loadCollectorStatus();
        loadMemoryTrail();
        setLlmInput('');
        
        // Scroll to results
        setTimeout(() => {
          resultRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to process response');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCollectorStatus = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/status/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setCurrentCollector(prev => ({ ...prev, ...data }));
      }
    } catch (err) {
      console.error('Error loading status:', err);
    }
  };

  const loadMemoryTrail = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/memory/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setMemoryTrail(data.memory_trail || []);
      }
    } catch (err) {
      console.error('Error loading memory trail:', err);
    }
  };

  const demonstrateRewind = async () => {
    if (!sessionId) {
      setError('Please create a collector session first');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/rewind`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          depth: 5
        })
      });

      if (response.ok) {
        const data = await response.json();
        setRewindResults(data.rewind_trail || []);
      }
    } catch (err) {
      setError('Error during rewind: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const demonstrateIteration = async () => {
    if (!sessionId) {
      setError('Please create a collector session first');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/iterator/next`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          depth: 3
        })
      });

      if (response.ok) {
        const data = await response.json();
        setIterationState(data);
      }
    } catch (err) {
      setError('Error during iteration: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const clearCollector = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/collector/clear/${sessionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setResults([]);
        setMemoryTrail([]);
        setRewindResults([]);
        setIterationState(null);
        loadCollectorStatus();
      }
    } catch (err) {
      setError('Error clearing collector: ' + err.message);
    }
  };

  const loadSampleResponse = (sample) => {
    setLlmInput(sample.content);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">
            🧠 LLM Memory Management Demo
          </h1>
          <p className="text-xl text-purple-200 mb-2">
            Advanced JSON Collection & Persistent Context Memory Layer
          </p>
          <p className="text-lg text-purple-300">
            Featuring FloJsonOutputCollector with Flo Q-Promise Looping
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-500 text-white p-4 rounded-lg mb-6">
            <strong>Error:</strong> {error}
            <button 
              onClick={() => setError('')}
              className="ml-4 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Session Management */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-4">🔧 Session Management</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-purple-300 mb-2">Session ID:</label>
              <input
                type="text"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="Enter session ID (e.g., demo-session)"
                className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500"
              />
            </div>
            
            <div className="flex items-center">
              <label className="flex items-center text-purple-300">
                <input
                  type="checkbox"
                  checked={strictMode}
                  onChange={(e) => setStrictMode(e.target.checked)}
                  className="mr-2"
                />
                Strict Mode (Require JSON)
              </label>
            </div>
          </div>

          <div className="flex gap-4 mb-4">
            <button
              onClick={createCollector}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Collector'}
            </button>
            
            <button
              onClick={clearCollector}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded"
            >
              Clear Memory
            </button>
          </div>

          {/* Current Collector Status */}
          {currentCollector && (
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="text-lg font-semibold text-white mb-2">Current Collector Status</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-purple-300">Status:</span>
                  <span className="text-white ml-2">{currentCollector.status}</span>
                </div>
                <div>
                  <span className="text-purple-300">Entries:</span>
                  <span className="text-white ml-2">{currentCollector.total_entries}</span>
                </div>
                <div>
                  <span className="text-purple-300">Trail Length:</span>
                  <span className="text-white ml-2">{currentCollector.memory_trail_length}</span>
                </div>
                <div>
                  <span className="text-purple-300">Strict Mode:</span>
                  <span className="text-white ml-2">{currentCollector.strict_mode ? 'Yes' : 'No'}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sample Responses */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-4">📝 Sample LLM Responses</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {sampleResponses.map((sample, index) => (
              <button
                key={index}
                onClick={() => loadSampleResponse(sample)}
                className="bg-gray-700 hover:bg-gray-600 p-4 rounded text-left transition-colors"
              >
                <h3 className="text-white font-semibold mb-2">{sample.name}</h3>
                <p className="text-gray-300 text-sm">
                  {sample.content.substring(0, 100)}...
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* LLM Response Input */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold text-white mb-4">🤖 Process LLM Response</h2>
          
          <div className="mb-4">
            <label className="block text-purple-300 mb-2">
              LLM Response (with mixed JSON content):
            </label>
            <textarea
              value={llmInput}
              onChange={(e) => setLlmInput(e.target.value)}
              placeholder="Paste LLM response with JSON content here... Comments with // and /* */ will be stripped automatically."
              rows={8}
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-purple-500"
            />
          </div>

          <button
            onClick={processLLMResponse}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Extract JSON & Store'}
          </button>
        </div>

        {/* Results Display */}
        {results.length > 0 && (
          <div ref={resultRef} className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-2xl font-semibold text-white mb-4">📊 Extraction Results</h2>
            <div className="space-y-4">
              {results.map((result) => (
                <div key={result.id} className="bg-gray-700 p-4 rounded">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-purple-300 text-sm">Input: {result.input}</span>
                    <span className="text-gray-400 text-sm">{result.timestamp}</span>
                  </div>
                  <div className="bg-gray-900 p-3 rounded">
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      {JSON.stringify(result.extracted, null, 2)}
                    </pre>
                  </div>
                  <div className="mt-2">
                    <span className={`text-sm px-2 py-1 rounded ${
                      result.status === 'success' ? 'bg-green-600' : 'bg-yellow-600'
                    }`}>
                      {result.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Advanced Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Rewind Demonstration */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-white mb-4">⏪ Rewind Demonstration</h2>
            <p className="text-purple-300 mb-4">
              Recursive Promise.then replay, newest→oldest entries
            </p>
            
            <button
              onClick={demonstrateRewind}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50 mb-4"
            >
              {loading ? 'Rewinding...' : 'Demonstrate Rewind'}
            </button>

            {rewindResults.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-white font-semibold">Rewind Trail:</h3>
                {rewindResults.map((item, index) => (
                  <div key={index} className="bg-gray-700 p-3 rounded text-sm">
                    <div className="text-purple-300">Step {index + 1}:</div>
                    <pre className="text-green-400 mt-1 overflow-x-auto">
                      {JSON.stringify(item.entry, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Iterator Demonstration */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-white mb-4">🔄 Iterator Demo</h2>
            <p className="text-purple-300 mb-4">
              Hybrid while–for iterator over memory steps
            </p>
            
            <button
              onClick={demonstrateIteration}
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded disabled:opacity-50 mb-4"
            >
              {loading ? 'Iterating...' : 'Next Iteration'}
            </button>

            {iterationState && (
              <div className="space-y-2">
                <h3 className="text-white font-semibold">Iterator State:</h3>
                <div className="bg-gray-700 p-3 rounded text-sm">
                  <div className="text-purple-300">Position: {iterationState.position.index}/{iterationState.position.total}</div>
                  <div className="text-purple-300">Has More: {iterationState.has_more ? 'Yes' : 'No'}</div>
                  <div className="text-purple-300">Remaining: {iterationState.position.remaining}</div>
                  
                  {iterationState.next_batch.length > 0 && (
                    <div className="mt-2">
                      <div className="text-purple-300">Current Batch:</div>
                      <pre className="text-green-400 mt-1 overflow-x-auto">
                        {JSON.stringify(iterationState.next_batch, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Memory Trail */}
        {memoryTrail.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-white mb-4">🗂️ Memory Breadcrumb Trail</h2>
            <div className="space-y-3">
              {memoryTrail.map((trail, index) => (
                <div key={index} className="bg-gray-700 p-4 rounded">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-purple-300 font-semibold">Entry #{index + 1}</span>
                    <span className="text-gray-400 text-sm">{trail.timestamp}</span>
                  </div>
                  <div className="text-sm text-gray-300 mb-2">
                    Raw Input: {trail.raw_output}
                  </div>
                  <div className="bg-gray-900 p-3 rounded">
                    <pre className="text-green-400 text-sm overflow-x-auto">
                      {JSON.stringify(trail.extracted_json, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active Sessions */}
        {activeSessions.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mt-6">
            <h2 className="text-2xl font-semibold text-white mb-4">🔗 Active Sessions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeSessions.map((session, index) => (
                <div key={index} className="bg-gray-700 p-4 rounded">
                  <h3 className="text-white font-semibold">{session.session_id}</h3>
                  <div className="text-sm text-purple-300 mt-2">
                    <div>Status: {session.status}</div>
                    <div>Entries: {session.total_entries}</div>
                    <div>Trail: {session.memory_trail_length}</div>
                    <div>Strict: {session.strict_mode ? 'Yes' : 'No'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-purple-300">
          <p>🚀 Demonstrating emergent work with IP trail maintenance</p>
          <p>Enhanced for ChatGPT, Gemini, Claude & distributed system architecture</p>
        </div>
      </div>
    </div>
  );
}

export default App;