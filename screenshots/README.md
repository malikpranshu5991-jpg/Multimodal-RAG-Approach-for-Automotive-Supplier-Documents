# Screenshot Checklist

Capture the following screenshots after the server is running successfully and after the Continental manual has been ingested.

## 1. Swagger UI
Open:

```powershell
start http://127.0.0.1:8000/docs
```

Save as: `01_swagger_ui.png`

## 2. Successful ingestion
Run:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/ingest" `
  -F "file=@sample_documents\continental_supplier_requirements_manual_2024.pdf"
```

Save the terminal output as: `02_ingest_success.png`

## 3. Supplier approval query result
Run:

```powershell
$body = @{ question = "What supplier approval prerequisites does Continental require?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/query" -Method Post -ContentType "application/json" -Body $body
```

Save as: `03_query_text.png`

## 4. Shipment document query result
Run:

```powershell
$body = @{ question = "What mandatory information must be included on the delivery note?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/query" -Method Post -ContentType "application/json" -Body $body
```

Save as: `04_query_table.png`

## 5. Quality / logistics query result
Run:

```powershell
$body = @{ question = "What emergency plan requirements does Continental place on suppliers?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/query" -Method Post -ContentType "application/json" -Body $body
```

Save as: `05_query_process.png`

## 6. Health endpoint
Run:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```

Save as: `06_health_endpoint.png`

## Cleanup step before screenshots

If you tested other PDFs earlier, clear the local index first so only the Continental manual is in the vector store:

```powershell
taskkill /F /IM python.exe
rmdir /S /Q data\chroma_db
rmdir /S /Q data\uploads
```

Then restart the app, ingest the sample PDF once, and capture the screenshots.
