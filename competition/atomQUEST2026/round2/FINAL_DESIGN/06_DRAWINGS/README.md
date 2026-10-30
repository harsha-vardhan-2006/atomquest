# Drawing sheets

21 sheets, one per native part and assembly, each carrying a third-angle view set
generated from the final CAD with `IDrawingDoc::Create3rdAngleViews2`.

| what is here | what is not |
|---|---|
| Real front/top/right/isometric views of the final geometry | dimensions, tolerances, surface finish notes |
| Correct model scale and units (millimetres) | drawing title block, BOM table, balloons |
| Exploded views: none | section views, detail views, weld/assembly notes |

Annotation insertion in this build requires the same sub-entity selection path that
fails for assembly mates, so the sheets are complete as *views* and incomplete as
*manufacturing drawings*. Open a sheet in SOLIDWORKS and use Insert > Model Items to
pull the model dimensions, then add the tolerances listed in
`../09_MANUFACTURING_GUIDE/MANUFACTURING_GUIDE.md`.
