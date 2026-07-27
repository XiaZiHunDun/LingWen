export interface Project {
  slug: string;
  name: string;
  role: string;
}

export interface Workflow {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Decision {
  id: string;
  title: string;
  status: 'pending' | 'approved' | 'rejected';
  workflow_id: string;
}

export interface RippleUpdate {
  type: string;
  payload: Record<string, unknown>;
}

export interface CascadeUpdate {
  ripple_id: string;
  cascade_node_count: number;
  cascade_edge_count: number;
  depth_reached: number;
  bfs_algorithm_version: string;
}