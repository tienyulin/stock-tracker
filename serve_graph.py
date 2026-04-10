#!/usr/bin/env python3
"""
Simple HTTP server for the wiki knowledge graph.
Usage: python serve_graph.py [port]
"""
import json
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
# In Docker, volume mounts at /app/graphify-out; fall back to host path
GRAPH_DIR = Path('/app/graphify-out') if Path('/app/graphify-out').exists() else Path('/Users/tienyu/stock-tracker/wiki/graphify-out')
GRAPH_JSON = GRAPH_DIR / 'graph.json'

def load_graph():
    data = json.loads(GRAPH_JSON.read_text())
    import networkx as nx
    from networkx.readwrite import json_graph
    G = json_graph.node_link_graph(data, edges='links', source='source', target='target')
    return G, data

def query_graph(G, question):
    question = question.lower()
    results = []
    for node in G.nodes():
        node_label = G.nodes[node].get('label', node).lower()
        if any(kw in node_label for kw in question.split()):
            results.append({
                'id': node,
                'label': G.nodes[node].get('label', node),
                'type': G.nodes[node].get('type', 'unknown'),
                'path': G.nodes[node].get('path', ''),
                'tags': G.nodes[node].get('tags', []),
                'neighbors': [
                    {'id': n, 'label': G.nodes[n].get('label', n)}
                    for n in G.neighbors(node)
                ]
            })
    return results

HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
<title>Wiki Knowledge Graph</title>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, system-ui, sans-serif; margin: 0; padding: 20px; background: #0d1117; color: #e6edf3; }
  h1 { color: #58a6ff; margin-bottom: 4px; }
  .subtitle { color: #8b949e; margin-bottom: 20px; font-size: 14px; }
  #graph { width: 100%; height: 480px; border: 1px solid #30363d; border-radius: 8px; background: #010409; margin-bottom: 16px; }
  .panel { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
  input { width: 100%; padding: 10px 14px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 14px; }
  input:focus { outline: none; border-color: #58a6ff; }
  .result-item { padding: 12px; background: #0d1117; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #58a6ff; }
  .result-item.type-concept { border-left-color: #3fb950; }
  .result-item.type-source { border-left-color: #f78166; }
  .result-label { font-weight: 600; font-size: 15px; }
  .result-path { color: #8b949e; font-size: 12px; }
  .tag { display: inline-block; background: #1f2937; padding: 1px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px; color: #9ca3af; }
  .neighbors { margin-top: 6px; font-size: 13px; color: #58a6ff; }
</style>
</head>
<body>
<h1>Wiki Knowledge Graph</h1>
<p class="subtitle" id="stats">Loading...</p>
<div id="graph"></div>
<div class="panel">
  <input type="text" id="q" placeholder="Search nodes... (press Enter)" />
  <div id="results"></div>
</div>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script>
var NODES, EDGES;

fetch('/graph.json').then(r=>r.json()).then(data=>{
  NODES = new vis.DataSet(data.nodes.map(n=>({
    ...n,
    color: { background: {file:'#58a6ff',concept:'#3fb950',source:'#f78166',entity:'#d2a8ff'}[n.type]||'#58a6ff' },
    title: (n.path||'')+(n.tags?'\\n'+n.tags.join(', '):'')
  })));
  EDGES = new vis.DataSet(data.edges);
  document.getElementById('stats').textContent = NODES.length + ' nodes · ' + EDGES.length + ' edges';
  var net = new vis.Network(document.getElementById('graph'), {nodes:NODES, edges:EDGES}, {
    physics: {forceAtlas2Based: {gravitationalConstant:-50, springLength:100}},
    interaction: {hover:true, navigationButtons:true}
  });
  net.on('click', p=>{ if(p.nodes[0]){document.getElementById('q').value=NODES.get(p.nodes[0]).label; doSearch(NODES.get(p.nodes[0]).label)} });
});

function doSearch(q) {
  if(!q) return;
  fetch('/query?q='+encodeURIComponent(q)).then(r=>r.json()).then(rs=>{
    document.getElementById('results').innerHTML = rs.length ? rs.map(r=>`
      <div class="result-item type-${r.type}">
        <div class="result-label">${r.label}</div>
        <div class="result-path">${r.path}</div>
        <div class="tags">${(r.tags||[]).map(t=>'<span class="tag">'+t+'</span>').join('')}</div>
        ${r.neighbors.length?'<div class="neighbors">→ '+r.neighbors.map(n=>n.label).join(', ')+'</div>':''}
      </div>`).join('') : '<p style="color:#8b949e">No results</p>';
  });
}
document.getElementById('q').addEventListener('keydown', e=>{ if(e.key==='Enter') doSearch(e.target.value); });
</script>
</body>
</html>'''

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif parsed.path == '/graph.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(GRAPH_JSON.read_bytes())
        elif parsed.path == '/query':
            params = parse_qs(parsed.query)
            q = params.get('q', [''])[0]
            G, _ = load_graph()
            results = query_graph(G, q)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results, ensure_ascii=False).encode())
        elif parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            super().do_GET()

if __name__ == '__main__':
    print(f'Starting on http://localhost:{PORT}')
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
