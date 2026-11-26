# SCAD authoring examples

The selected reference scenes and `kit_layout.scad` / `kit_terrain.scad` are adapted from gkNextEngine, Copyright (c) 2024–2026 gameknife, MIT licensed. See LICENSE and provenance.json for the source paths and original byte hashes. Only SCAD source and its transitive SCAD dependencies are redistributed here; no upstream binaries, textures, fonts or third-party native libraries are included.

Adaptations: gk host calls renamed to world; terrain tag migrated; engine-camera directives removed because the editor owns cameras; entry dependency paths relocated and bounds/seed supplied. Azure Harbor and Forest Crossroads retain their compositions. The ecocity entry is a new curated four-block composition using unchanged upstream component geometry; the complete city source is retained as a use library, not executed automatically. These are visual references, not existing GDD inventories or pre-approved gameplay maps.

The new initialization examples and kit_environment.scad are project-authored examples distributed under the same MIT terms. The examples do not provide Module resource IDs. Hosts continue to use the existing trusted inventory and map/placement contracts.

overview.png files are screenshots produced by the editor's Three.js renderer from the accompanying reference sources. The SCAD source inventory and SHA-256 checksums are also recorded in sbom.spdx.json; compiler and third-party binary SBOMs remain owned by scad-three-runtime.

The seven studies in studies/ are dependency-closed excerpts from the user's
specified successful reconstruction artifacts, including three proc scene
sources from gkNextEngine. case-studies.json records each original source hash and lists the included declarations. Their scene.scad assemblies
are local demonstrations, not copies of the complete original maps.
Original finished-scene images, local screenshots, Blender scene files, rendering
scripts, generated full-scene mesh arrays and external Python generators are not
redistributed with these studies.
