import {
  Background,
  Controls,
  Handle,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { flattenTree, nodeTitle, statusColor, type NodeLike } from '../utils/trace'

interface TraceDagProps {
  root: NodeLike
  onSelect: (id: string) => void
}

interface DagNodeData {
  label: string
  status: string
  type: string
  [key: string]: unknown
}

function DagNode({ data, selected }: NodeProps<Node<DagNodeData>>) {
  const color = statusColor(data.status)
  return (
    <div
      data-testid="dag-node"
      className={`min-w-36 rounded-lg border bg-surface px-3 py-2 text-xs shadow-sm ${
        selected ? 'border-accent ring-2 ring-accent/30' : 'border-line'
      }`}
    >
      <Handle type="target" position={Position.Left} />
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: color }} />
        <span className="truncate font-medium text-ink" title={data.label}>
          {data.label}
        </span>
      </div>
      <span className="text-faint">{data.type}</span>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

export default function TraceDag({ root, onSelect }: TraceDagProps) {
  const rows = flattenTree(root)
  const nodes: Node<DagNodeData>[] = rows.map((row, index) => ({
    id: row.id,
    type: 'dagNode',
    position: { x: row.depth * 260, y: index * 72 },
    data: {
      label: nodeTitle(row),
      status: row.status,
      type: row.type,
    },
  }))
  const edges: Edge[] = rows
    .filter((row) => row.parent_id)
    .map((row) => ({
      id: `e-${row.parent_id}-${row.id}`,
      source: row.parent_id as string,
      target: row.id,
      type: 'smoothstep',
      animated: row.status === 'running',
      style: { stroke: 'var(--color-faint)' },
    }))

  return (
    <div className="h-full" data-testid="dag">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ dagNode: DagNode }}
        onNodeClick={(_, node) => onSelect(node.id)}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
      >
        <Background color="var(--color-line)" gap={24} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}
