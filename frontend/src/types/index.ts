export interface FunctionInfo {
  key: string;
  name: string;
  line: number;
  has_predictions: boolean;
}

export interface FunctionTree {
  [directory: string]: {
    [filename: string]: FunctionInfo[];
  } | FunctionTree;
}

export interface GraphNode {
  id: string;
  label: string;
  file: string;
  line: number;
  hasContract: boolean;
  hasPredictions: boolean;
  abstractionLevel: string;
  fileColor: string;
  isCenter: boolean;
  level: number;
}

export interface GraphEdge {
  from: string;
  to: string;
}

export interface FunctionGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  center: string;
}

export interface FunctionCode {
  code: string;
  language: string;
  start_line: number;
  end_line: number;
  callers: string[];
  callees: string[];
  function_name: string;
  graph_callers?: string[];
  graph_callees?: string[];
}

export interface FunctionContract {
  name: string;
  file_path: string;
  line_number: number;
  preconditions: string[];
  postconditions: string[];
  input_prediction: string;
  output_prediction: string;
  expected_behavior: string;
  abstraction_level: string;
  metadata: Record<string, any>;
}
