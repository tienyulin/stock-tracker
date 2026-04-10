#!/usr/bin/env python3
"""
Build a knowledge graph from the wiki markdown files.
Output format compatible with networkx node_link_graph.
"""
import json
import re
from pathlib import Path
from datetime import datetime

# Detect if running in container or host
HOST_WIKI = Path('/Users/tienyu/stock-tracker/wiki')
CONTAINER_WIKI = Path('/app/wiki')

if CONTAINER_WIKI.exists():
    WIKI_ROOT = CONTAINER_WIKI
else:
    WIKI_ROOT = HOST_WIKI

OUT_PATH = WIKI_ROOT / 'graphify-out/graph.json'

def extract_links(content):
    """Extract markdown links from content."""
    return re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)

def extract_entities(content):
    """Extract potential entities from content."""
    entities = set()
    headers = re.findall(r'^##?\s+(.+)$', content, re.MULTILINE)
    for h in headers:
        entities.add(h.strip())
    bolds = re.findall(r'\*\*([^\*]+)\*\*', content)
    for b in bolds:
        entities.add(b.strip())
    return entities

def build_graph():
    pages_dir = WIKI_ROOT / 'pages'
    raw_dir = WIKI_ROOT / 'raw'

    nodes = []
    links = []
    node_id = 0

    # Map from file stem to node id
    stem_to_nid = {}

    # Create a node for each file
    all_files = list(pages_dir.rglob('*.md')) + list(raw_dir.rglob('*.md'))

    for fpath in all_files:
        rel_path = fpath.relative_to(WIKI_ROOT)
        content = fpath.read_text()

        fname = fpath.stem
        nid = f'node_{node_id}'
        stem_to_nid[fname] = nid

        node = {
            'id': nid,
            'label': fname,
            'type': 'file',
            'path': str(rel_path),
            'tags': []
        }

        # Add frontmatter tags
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            tags_match = re.findall(r'tags:\s*\[(.*?)\]', fm, re.DOTALL)
            if tags_match:
                node['tags'] = [t.strip() for t in tags_match[0].split(',')]

        nodes.append(node)
        node_id += 1

        # Extract links from content and create edges
        for link_text, link_target in extract_links(content):
            if link_target.startswith('http'):
                continue
            try:
                link_path = (fpath.parent / link_target).resolve()
                if link_path.exists() and link_path.suffix == '.md':
                    target_stem = link_path.stem
                    if target_stem in stem_to_nid:
                        links.append({
                            'source': nid,
                            'target': stem_to_nid[target_stem],
                            'relation': 'links_to',
                            'label': link_text
                        })
            except Exception:
                pass

    # Create cross-references between pages
    entity_map = {}  # entity -> list of (file_stem, node_id)

    for fpath in all_files:
        content = fpath.read_text()
        entities = extract_entities(content)
        for entity in entities:
            if entity not in entity_map:
                entity_map[entity] = []
            entity_map[entity].append((fpath.stem, stem_to_nid[fpath.stem]))

    # Connect files that share entities
    for entity, files in entity_map.items():
        if len(files) > 1:
            seen = set()
            for i in range(len(files)):
                for j in range(i+1, len(files)):
                    key = tuple(sorted([files[i][1], files[j][1]]))
                    if key not in seen:
                        seen.add(key)
                        links.append({
                            'source': files[i][1],
                            'target': files[j][1],
                            'relation': 'shares_entity',
                            'label': entity
                        })

    graph = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'source': 'wiki',
            'files': len(all_files)
        },
        'nodes': nodes,
        'links': links
    }

    return graph

if __name__ == '__main__':
    graph = build_graph()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(graph, indent=2))
    print(f"Graph built: {len(graph['nodes'])} nodes, {len(graph['links'])} links")
    print(f"Written to: {OUT_PATH}")
