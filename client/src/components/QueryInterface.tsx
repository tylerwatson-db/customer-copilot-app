import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

interface QueryResponse {
  response: string
  metadata: {
    responseTime: number
    timestamp: string
    endpoint: string
  }
  error?: string
}

interface QueryResult extends QueryResponse {
  id: string
  query: string
}

export function QueryInterface() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<QueryResult[]>([])

  const queryMutation = useMutation({
    mutationFn: async (queryText: string): Promise<QueryResponse> => {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: queryText }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return response.json()
    },
    onSuccess: (data, queryText) => {
      const result: QueryResult = {
        ...data,
        id: Date.now().toString(),
        query: queryText,
      }
      setResults(prev => [...prev, result])
      setQuery('')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      queryMutation.mutate(query.trim())
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const formatResponseTime = (time: number) => {
    return `${time.toFixed(2)}s`
  }

  return (
    <div className="container mx-auto max-w-4xl p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Customer Copilot Query Interface</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex space-x-2">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about customer calls..."
                disabled={queryMutation.isPending}
                className="flex-1"
              />
              <Button 
                type="submit" 
                disabled={queryMutation.isPending || !query.trim()}
              >
                {queryMutation.isPending ? 'Processing...' : 'Submit'}
              </Button>
            </div>
            
            {queryMutation.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  Error: {queryMutation.error?.message}
                </AlertDescription>
              </Alert>
            )}
          </form>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Query Results</h2>
          {results.map((result) => (
            <Card key={result.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">
                    {result.query}
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(result.response)}
                  >
                    Copy
                  </Button>
                </div>
                <div className="flex space-x-2 text-sm text-muted-foreground">
                  <Badge variant="secondary">
                    {formatResponseTime(result.metadata.responseTime)}
                  </Badge>
                  <span>{formatTimestamp(result.metadata.timestamp)}</span>
                </div>
              </CardHeader>
              <CardContent>
                {result.error ? (
                  <Alert variant="destructive">
                    <AlertDescription>{result.error}</AlertDescription>
                  </Alert>
                ) : (
                  <div className="whitespace-pre-wrap text-sm">
                    {result.response}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}