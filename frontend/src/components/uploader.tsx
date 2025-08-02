import React, { useState } from 'react'

export default function Uploader() {
  const [file, setFile] = useState<File|null>(null)
  const upload = async () => {
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    await fetch('http://localhost:8000/upload', { method: 'POST', body: fd })
  }

  return (
    <div className="uploader">
      <input type="file" onChange={e => e.target.files && setFile(e.target.files[0])} />
      <button onClick={upload}>Upload</button>
    </div>
  )
}