import { useState } from 'react'
import { login } from '../api'

type Props = { onSuccess: () => void }

export default function LoginPage({ onSuccess }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      await login(email.trim(), password)
      onSuccess()
    } catch (e: any) {
      setError(e?.message ?? 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h2>Sign in</h2>
        <label>Email</label>
        <input type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)} required/>
        <label>Password</label>
        <input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required/>
        {error && <div className="auth-error">{error}</div>}
        <button type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
      </form>
    </div>
  )
}
