import React, { useState } from 'react'

interface ChatProps {
  messages: any[];
  onSend: (prompt: string) => void;
}

export default function Chat({ messages, onSend }: ChatProps) {
  const [input, setInput] = useState('')
  const send = () => { onSend(input); setInput('') }

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={m.type || 'ai'}>
            {m.text || (m.type === 'chart_ready' ? <img src={m.url} alt="chart" /> : m.code)}
          </div>
        ))}
      </div>
      <div className="input">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
        />
        <button onClick={send}>Send</button>
      </div>
    </div>
  )
}