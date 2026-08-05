import { buildTimeline, statusColor, type NodeLike } from '../utils/trace'

interface TimelineProps {
  root: NodeLike
  onSelect: (id: string) => void
  selectedId: string | null
}

export default function Timeline({ root, onSelect, selectedId }: TimelineProps) {
  const segments = buildTimeline(root)
  const maxEnd = Math.max(1, ...segments.map((s) => s.startMs + s.durationMs))

  return (
    <div className="flex flex-col gap-1 p-3" data-testid="timeline">
      {segments.length === 0 && <p className="text-xs text-faint">无时间线数据</p>}
      {segments.map((seg) => (
        <button
          key={seg.id}
          data-testid="timeline-bar"
          onClick={() => onSelect(seg.id)}
          className={`flex items-center gap-2 text-left ${selectedId === seg.id ? 'opacity-100' : 'opacity-70 hover:opacity-100'}`}
        >
          <span className="w-28 shrink-0 truncate text-xs text-muted" style={{ paddingLeft: seg.depth * 8 }}>
            {seg.name}
          </span>
          <span className="relative h-4 flex-1 rounded-sm bg-canvas">
            <span
              className="absolute top-0 h-full rounded-sm"
              style={{
                left: `${(seg.startMs / maxEnd) * 100}%`,
                width: `${Math.max(1, (seg.durationMs / maxEnd) * 100)}%`,
                background: statusColor(seg.status),
              }}
            />
          </span>
          <span className="w-16 shrink-0 text-right text-xs tabular-nums text-faint">
            {(seg.durationMs / 1000).toFixed(1)}s
          </span>
        </button>
      ))}
    </div>
  )
}
