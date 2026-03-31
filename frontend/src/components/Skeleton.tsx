import './Skeleton.css'

interface SkeletonProps {
  width?: string
  height?: string
  borderRadius?: string
  className?: string
}

export function Skeleton({ width = '100%', height = '20px', borderRadius = '4px', className = '' }: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius }}
    />
  )
}

export function StockCardSkeleton() {
  return (
    <div className="stock-card-skeleton">
      <div className="skeleton-header">
        <Skeleton width="80px" height="20px" />
        <Skeleton width="60px" height="16px" borderRadius="12px" />
      </div>
      <Skeleton width="120px" height="32px" borderRadius="4px" className="skeleton-price" />
      <Skeleton width="100px" height="14px" />
    </div>
  )
}
