# Report Delivery Runbook (Option A + B)

## Overview
This pipeline uploads report artifacts to S3, generates expiring signed URLs for every asset, rewrites the hosted HTML to use those signed URLs, and emails the recipient with the PDF attached plus the interactive link.

## Expected Bundle Layout
Place the report output in a clean directory (no unrelated files). Minimum required files:
- report.html
- report.pdf
Optional but recommended:
- report-data.json
- source/exhibit PDFs
- assets (CSS/JS/fonts/images)

Hosted HTML should reference `report-data.json` via a placeholder:
- `__REPORT_DATA_URL__` (replaced with signed URL)
- `__REPORT_PDF_URL__` (optional, replaced with signed URL)

If `report.html` still embeds bulk data in a `<script id="report-data" type="application/json">` block, set `externalize_data: true` in config to extract it into `report-data.json` and inject a loader snippet.
The loader sets `window.__REPORT_DATA_PROMISE__` and fires a `report-data-ready` event; ensure your JS waits for data before rendering.

## Prereqs
- AWS credentials in the environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- S3 bucket created (private)
- SMTP credentials for outbound email

Install dependencies:
```
pip install -r ops/report_delivery/requirements.txt
```

## Configure
Copy and edit:
- `ops/report_delivery/config.example.json`

Set `SMTP_PASSWORD` in env if using `password_env`.
Ensure the S3 bucket CORS policy allows GET from the report origin if you serve via a custom domain/CDN.

## Run
```
python ops/report_delivery/report_delivery.py ops/report_delivery/config.example.json
```
Outputs:
- Signed URLs embedded into hosted HTML/JS/CSS
- Email sent with PDF attached (if <= `attach_max_bytes`) and hosted link
- `hosted_links.json` created in the bundle directory
- `report-data.json` created if `externalize_data` is enabled and an inline block is detected
- `token_id` stored in `hosted_links.json` for log correlation

## Reissue Links
Re-run the script with the same `report_id` and a new expiration:
- Set `expires_in` to the new TTL
- Re-send the email using the updated `hosted_links.json`

## Revoke Access
One of:
1) Delete the report prefix in S3: `reports/<report_id>/`
2) Rotate/disable the AWS key used for signing
3) Remove hosted artifacts and re-upload with a new report_id

## Access Logging (Optional)
Baseline:
- Enable S3 server access logs or CloudFront logs for the bucket.

Optional view logging:
- Provide `access_log.log_url` to inject a 1x1 pixel call on HTML load.
- If `wrap_pdf_links` is true, the log endpoint must redirect to the `redirect` URL.
Quick local endpoint:
```
python ops/report_delivery/access_log_server.py --port 8080
```

Recommended log fields:
- report_id
- token_id
- event (view, download_pdf)
- timestamp (from server access logs)
- IP/user-agent (from server access logs)

## QA Checklist
- Verify report.html loads and JS/CSS/PDFs resolve under signed URLs
- Open report.pdf attachment in common clients
- Confirm signed URLs expire after TTL
- Test on iOS Safari/Chrome, Android Chrome, iPad, desktop Chrome/Edge/Safari

## Notes
- Signed URLs are rewritten into HTML/JS/CSS for private buckets. Avoid cache-busting query params in asset paths for hosted mode.
- If report.html still embeds bulk data, update the generator to fetch `report-data.json` at runtime.
