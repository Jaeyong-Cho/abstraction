import type {
  FunctionTree,
  FunctionGraph,
  FunctionCode,
  FunctionContract,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function encodeFunctionKey(key: string): string {
  if (!key) return '';
  
  // Find the first :: separator (file_path::function_name)
  // For C++ classes, function_name may contain :: (e.g., MyClass::method)
  const firstSeparatorIndex = key.indexOf('::');
  if (firstSeparatorIndex === -1) {
    // No separator found, just encode and remove leading slash
    let encoded = encodeURIComponent(key);
    if (encoded.startsWith('/')) {
      encoded = encoded.substring(1);
    }
    return encoded;
  }
  
  // Split at first :: only
  const filePath = key.substring(0, firstSeparatorIndex);
  const functionName = key.substring(firstSeparatorIndex + 2); // Skip '::'
  
  // Remove leading slash, encode path segments separately
  const pathWithoutLeadingSlash = filePath.startsWith('/') 
    ? filePath.substring(1) 
    : filePath;
  
  // Encode each path segment separately to preserve /
  const encodedPath = pathWithoutLeadingSlash
    .split('/')
    .map(segment => encodeURIComponent(segment))
    .join('/');
  
  // Encode function name (may contain :: for C++ classes)
  // encodeURIComponent will encode :: to %3A%3A automatically
  const encodedFunctionName = encodeURIComponent(functionName);
  
  return `${encodedPath}%3A%3A${encodedFunctionName}`;
}

export async function getFunctionTree(): Promise<{ tree: FunctionTree }> {
  const response = await fetch(`${API_BASE_URL}/api/functions`);
  if (!response.ok) {
    throw new Error(`Failed to load function tree: ${response.statusText}`);
  }
  return response.json();
}

export async function getFunctionGraph(
  functionKey: string
): Promise<FunctionGraph> {
  const encodedKey = encodeFunctionKey(functionKey);
  const response = await fetch(
    `${API_BASE_URL}/api/function-graph/${encodedKey}`
  );
  if (!response.ok) {
    throw new Error(`Failed to load function graph: ${response.statusText}`);
  }
  return response.json();
}

export async function getFunctionCode(
  functionKey: string
): Promise<FunctionCode> {
  const encodedKey = encodeFunctionKey(functionKey);
  const response = await fetch(
    `${API_BASE_URL}/api/function-code/${encodedKey}`
  );
  if (!response.ok) {
    throw new Error(`Failed to load function code: ${response.statusText}`);
  }
  return response.json();
}

export async function getFunctionContract(
  functionKey: string
): Promise<FunctionContract | null> {
  const encodedKey = encodeFunctionKey(functionKey);
  const response = await fetch(`${API_BASE_URL}/api/contract/${encodedKey}`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to load contract: ${response.statusText}`);
  }
  return response.json();
}

export async function saveFunctionContract(
  functionKey: string,
  contract: Partial<FunctionContract>
): Promise<{ success: boolean; message?: string; error?: string; contract?: FunctionContract }> {
  const encodedKey = encodeFunctionKey(functionKey);
  const response = await fetch(`${API_BASE_URL}/api/contract/${encodedKey}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(contract),
  });
  return response.json();
}

export async function getWorkspace(): Promise<{ workspace: string }> {
  const response = await fetch(`${API_BASE_URL}/api/workspace`);
  if (!response.ok) {
    throw new Error(`Failed to load workspace: ${response.statusText}`);
  }
  return response.json();
}

export async function setWorkspace(
  path: string
): Promise<{ success: boolean; workspace?: string; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/workspace`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ path }),
  });
  return response.json();
}

export async function indexWorkspace(): Promise<{
  success: boolean;
  count?: number;
  message?: string;
  error?: string;
}> {
  const response = await fetch(`${API_BASE_URL}/api/index`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return response.json();
}
