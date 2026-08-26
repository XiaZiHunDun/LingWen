export function useWorldReview() {
  async function listProposals(status) {
    const url = status
      ? `/api/world/proposals?status=${encodeURIComponent(status)}`
      : '/api/world/proposals'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`listProposals failed: ${res.statusText}`)
    return (await res.json()).proposals
  }

  async function submitProposal(payload) {
    const res = await fetch('/api/world/proposals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`submitProposal failed: ${res.statusText}`)
    return res.json()
  }

  async function acceptProposal(id, reviewer) {
    const res = await fetch(`/api/world/proposals/${id}/accept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer }),
    })
    if (!res.ok) throw new Error(`acceptProposal failed: ${res.statusText}`)
    return res.json()
  }

  async function rejectProposal(id, reviewer) {
    const res = await fetch(`/api/world/proposals/${id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer }),
    })
    if (!res.ok) throw new Error(`rejectProposal failed: ${res.statusText}`)
    return res.json()
  }

  return { listProposals, submitProposal, acceptProposal, rejectProposal }
}