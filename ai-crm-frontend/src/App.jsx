import { useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

function App() {
  const [message, setMessage] = useState("");
  const [hcpName, setHcpName] = useState("");
  const [interactionId, setInteractionId] = useState("");

  const [chatResponse, setChatResponse] = useState(null);
  const [history, setHistory] = useState([]);
  const [interaction, setInteraction] = useState(null);

  const sendChat = async () => {
    try {
      const res = await axios.post(`${API}/chat`, {
        message,
      });
      setChatResponse(res.data);
    } catch (err) {
      alert("Chat failed");
    }
  };

  const logInteraction = async () => {
    try {
      const res = await axios.post(`${API}/log`, {
        message,
      });
      setChatResponse(res.data);
    } catch (err) {
      alert("Logging failed");
    }
  };

  const getHistory = async () => {
    try {
      const res = await axios.get(`${API}/history/${hcpName}`);
      setHistory(res.data);
    } catch (err) {
      alert("History not found");
    }
  };

  const getInteraction = async () => {
    try {
      const res = await axios.get(
        `${API}/interaction/${interactionId}`
      );
      setInteraction(res.data);
    } catch (err) {
      alert("Interaction not found");
    }
  };

  return (
  <div className="container">

    <h1>AI First CRM</h1>

    <div className="section">

      <h2>AI Assistant</h2>

      <textarea
        rows={8}
        placeholder="Describe HCP interaction..."
        value={message}
        onChange={(e)=>setMessage(e.target.value)}
      />

      <button onClick={sendChat}>
        Run AI Agent
      </button>

      <button onClick={logInteraction}>
        Log Interaction
      </button>

    </div>

    <div className="section">

      <h2>Search History</h2>

      <input
        placeholder="Doctor Name"
        value={hcpName}
        onChange={(e)=>setHcpName(e.target.value)}
      />

      <button onClick={getHistory}>
        Search
      </button>

      <pre>
        {JSON.stringify(history,null,2)}
      </pre>

    </div>

    <div className="section">

      <h2>Interaction Details</h2>

      <input
        placeholder="Interaction ID"
        value={interactionId}
        onChange={(e)=>setInteractionId(e.target.value)}
      />

      <button onClick={getInteraction}>
        Get Interaction
      </button>

      <pre>
        {JSON.stringify(interaction,null,2)}
      </pre>

    </div>

    <div className="section">

      <h2>AI Response</h2>

      <pre>
        {JSON.stringify(chatResponse,null,2)}
      </pre>

    </div>

  </div>
);
}

export default App;