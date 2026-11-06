/* Positions only: preserve Neo4j node names, directed edges and document identifiers. */
(function (root) {
  'use strict';

  function layout(edges, width = 900, height = 540) {
    const names = [...new Set(edges.flatMap(e => [e.source, e.target]))].sort();
    const adjacency = new Map(names.map(name => [name, new Set()]));
    edges.forEach(e => {
      adjacency.get(e.source).add(e.target);
      adjacency.get(e.target).add(e.source);
    });
    const seen = new Set(), components = [];
    for (const name of names) {
      if (seen.has(name)) continue;
      const members = [], queue = [name];
      seen.add(name);
      while (queue.length) {
        const current = queue.pop();
        members.push(current);
        for (const next of [...adjacency.get(current)].sort()) {
          if (!seen.has(next)) { seen.add(next); queue.push(next); }
        }
      }
      components.push(members.sort());
    }
    components.sort((a, b) => b.length - a.length || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
    if (!components.length) return {nodes: [], components: []};
    const columns = Math.min(components.length, Math.ceil(Math.sqrt(components.length * width / height)));
    const rows = Math.ceil(components.length / columns), cellWidth = width / columns, cellHeight = height / rows;
    const nodes = [];
    components.forEach((members, group) => {
      const local = members.map((name, i) => ({name,
        x: Math.cos(i * Math.PI * 2 / members.length) * 30,
        y: Math.sin(i * Math.PI * 2 / members.length) * 30}));
      const byName = new Map(local.map(n => [n.name, n]));
      const localEdges = edges.filter(e => byName.has(e.source) && byName.has(e.target));
      // Small, deterministic spring layouts inside each actual connected component.
      for (let step = 0; step < 180; step++) {
        const forces = local.map(n => ({x: -n.x * .015, y: -n.y * .015}));
        for (let i = 0; i < local.length; i++) {
          for (let j = i + 1; j < local.length; j++) {
            let dx = local[i].x - local[j].x, dy = local[i].y - local[j].y;
            if (Math.abs(dx) + Math.abs(dy) < .001) { dx = .1 * (i + 1); dy = .1; }
            const distance = Math.max(1, Math.hypot(dx, dy)), force = 1000 / (distance * distance);
            forces[i].x += dx / distance * force; forces[i].y += dy / distance * force;
            forces[j].x -= dx / distance * force; forces[j].y -= dy / distance * force;
          }
        }
        for (const edge of localEdges) {
          const a = byName.get(edge.source), b = byName.get(edge.target);
          const dx = b.x - a.x, dy = b.y - a.y, distance = Math.max(1, Math.hypot(dx, dy));
          const force = (distance - 34) * .07, i = local.indexOf(a), j = local.indexOf(b);
          forces[i].x += dx / distance * force; forces[i].y += dy / distance * force;
          forces[j].x -= dx / distance * force; forces[j].y -= dy / distance * force;
        }
        local.forEach((n, i) => {
          n.x += Math.max(-2, Math.min(2, forces[i].x));
          n.y += Math.max(-2, Math.min(2, forces[i].y));
        });
      }
      const minX = Math.min(...local.map(n => n.x)), maxX = Math.max(...local.map(n => n.x));
      const minY = Math.min(...local.map(n => n.y)), maxY = Math.max(...local.map(n => n.y));
      const scale = Math.min((cellWidth - 36) / Math.max(maxX - minX, 35), (cellHeight - 32) / Math.max(maxY - minY, 35));
      const occupied = Math.min(columns, components.length - Math.floor(group / columns) * columns);
      const offsetX = (width - occupied * cellWidth) / 2;
      const cx = (group % columns + .5) * cellWidth + offsetX, cy = (Math.floor(group / columns) + .5) * cellHeight;
      local.forEach(n => nodes.push({name: n.name, group,
        x: cx + (n.x - (minX + maxX) / 2) * scale,
        y: cy + (n.y - (minY + maxY) / 2) * scale}));
    });
    return {nodes, components};
  }
  root.GlucoGraph = Object.freeze({layout});
  if (typeof module !== 'undefined' && module.exports) module.exports = root.GlucoGraph;
})(globalThis);
