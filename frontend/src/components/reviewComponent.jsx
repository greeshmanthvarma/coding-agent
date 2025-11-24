import React from 'react'
import { useState, useEffect } from 'react'

export default function reviewComponent({ reviewId }) {
  const [review, setReview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchReview = async () => {
      try {
        const response = await fetch(`/api/agent/review/${reviewId}`)
        const data = await response.json()
        setReview(data)
      } catch (error) {
        setError(error)
      }
    }
  }, [])

  return (
    <div>
        {loading && <div>Loading...</div>}
        {error && <div>Error: {error}</div>}
        {review && <div>{review.changes}</div>}
    </div>
  )
}