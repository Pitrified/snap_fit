# ingest pieces and matches into a db

in
scratch_space/fastapi_scaffold/README.md
we have the setup plan for a fastapi app for the snap_fit project.

in
docs/getting_started.md
we have a logical progression of steps to do to ingest data and use the snap_fit library

a preliminary step before the fastapi app is to setup the ingestion of pieces and matches into a database,
which will then be ingested and queried by the fastapi app.

we need to cover the steps related to
1. SheetManager loading of the sheets and pieces
2. PieceMatcher matching of the pieces

this is the purpose of this document.
