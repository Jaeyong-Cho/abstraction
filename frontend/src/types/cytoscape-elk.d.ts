declare module 'cytoscape-elk' {
  import cytoscape from 'cytoscape';
  export default function register(cytoscape: typeof cytoscape): void;
}
