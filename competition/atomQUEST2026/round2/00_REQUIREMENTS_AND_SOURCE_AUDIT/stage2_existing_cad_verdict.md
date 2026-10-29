# Stage 2 verdict — the 17 existing parts are unusable as CAD

Method: every `.SLDPRT` opened with `OpenDoc6`, rebuilt with `EditRebuild3`,
then measured with `IPartDoc.GetPartBox(True)` (API units = metres),
`IPartDoc.GetBodies2` and `IBody2.GetMassProperties`.
Raw output: `existing_cad_audit.csv`, `existing_cad_audit.log`.
Environment: `environment_report.md` (SOLIDWORKS 34.4.1, typed pythonnet interop).

## Findings (all 17 parts, without exception)

| Check | Result |
| --- | --- |
| Opens without error | PASS — all 17 open, `rebuild_ok = True`, zero rebuild errors |
| Contains 3D geometry | **FAIL — `n_bodies = 0` for every part** |
| Feature tree | only `Front/Top/Right Plane`, `Origin`, `Sketch1` (+`Sketch2` on the ring/shell parts). **No boss-extrude, no cut, no revolve, no hole** |
| Bounding box Z | **0.000 m for all 17 parts** — the geometry is a flat sketch, not a solid |
| Scale | **~1000× oversized.** e.g. `M1_CeilingPlate` sketch spans 300 **metres** (labelled 300 mm); `M1_OuterRing` spans 1200 m (labelled 600 OD) |
| Diameter vs radius | **2× error on top of the scale error** — `SM_create_circle(dia)` passed the value where `CreateCircle` expects a radius |

Interpretation: `create_cad_models.py` drew the sketches (that part of the API
call worked) but every `FeatureExtrusion` silently failed — it was invoked with
15 arguments on `IModelDoc2` while the method with that signature lives on
`IPartDoc`, and its return value was never checked. The script then "saved" the
files and printed byte counts, so the run looked successful.

Evidence consistent with the Stage 1 static findings:

1. `create_cad_models.py:99` — `return new_part(doc=None)def save(doc, path):` (syntax error; the committed script cannot run at all).
2. `part_extrude(..., cut=False)` never reads `cut`, so `make_pipe()` could not have produced a bore even if the extrude had worked.
3. `SM_create_circle(sm, dia)` passes a diameter as a radius.
4. Model READMEs claim "CAD status: NOT STARTED" while 17 placeholder files exist; `02_CAD_ASSEMBLIES/` is empty.

## Decision (documented reason for replacing existing work)

The parts contain **no solid geometry and no usable dimensions** — there is
nothing to reuse beyond the part *names*, the nominal dimensions printed in the
model READMEs and the folder structure. Rebuilding them from the frozen design
values is therefore justified; no verified engineering content is discarded.
Existing files are kept on disk until their replacements are written, and this
report is the audit trail for that decision.

## What Stage 3+ must therefore do

- Model in **metres** (API convention), all nominal sizes divided correctly (mm/1000).
- Use `IPartDoc.FeatureExtrusion3` (18 args) for bosses and `IModelDoc2.FeatureCut5` for bores — with the return/feature result checked, never assumed.
- Verify every part after creation by reopening it, rebuilding it, and confirming `n_bodies >= 1`, a non-zero Z extent and a sane bounding box before it is accepted.
- Mark every part **PRELIMINARY** where the driving dimension is an assumption (blade section, motor envelope, servo pattern, bearing fits).
