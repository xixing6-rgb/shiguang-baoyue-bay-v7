return await (async function inspectAssembled(scene) {
  const roots = ["n2", "n79", "n88", "n101", "n143", "n153", "n207", "n215", "n253"];
  const out = {};
  for (const r of roots) {
    const q = await scene.nodes.query({ subtree: r }, { fields: ["handle", "name", "parent", "layer", "componentTypes"], limit: 100 });
    out[r] = q.items.map(i => ({ h: i.handle, n: i.name, p: i.parent, l: i.layer, c: i.componentTypes }));
  }
  const b = await scene.scripts.bindings(roots, { limit: 100 });
  return { out, bindings: b.items };
})(scene);
