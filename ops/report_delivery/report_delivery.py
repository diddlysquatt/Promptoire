from __future__ import annotations

import json
import mimetypes
import os
import re
import secrets
import smtplib
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlsplit, urlunsplit

try:
    import boto3
except Exception:  # pragma: no cover - optional dependency
    boto3 = None

TEXT_EXTENSIONS = {".html", ".css", ".js"}
SKIP_FILENAMES = {"report_offline.zip"}
REPORT_DATA_SCRIPT_RE = re.compile(
    r'(<script[^>]*\bid=["\']report-data["\'][^>]*>)(?P<content>.*?)(</script>)',
    re.IGNORECASE | re.DOTALL,
)
REPORT_DATA_LOADER = (
    "<script>"
    "window.__REPORT_DATA_URL__=\"__REPORT_DATA_URL__\";"
    "window.__REPORT_DATA_PROMISE__=fetch(window.__REPORT_DATA_URL__)"
    ".then(function(response){return response.json();})"
    ".then(function(data){window.__REPORT_DATA__=data;"
    "window.dispatchEvent(new Event(\"report-data-ready\"));return data;})"
    ".catch(function(error){console.error(\"Failed to load report data\", error);});"
    "</script>"
)


@dataclass
class ReportBundle:
    base_dir: Path
    report_id: str
    report_html: Path
    report_pdf: Path
    files: List[Path]

    def relative_path(self, path: Path) -> str:
        return path.relative_to(self.base_dir).as_posix()


@dataclass
class S3Config:
    bucket: str
    prefix: str
    region: Optional[str] = None
    endpoint_url: Optional[str] = None


@dataclass
class EmailConfig:
    sender: str
    recipients: List[str]
    subject: str
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    reply_to: Optional[str] = None
    attach_max_bytes: int = 15_000_000
    contact: Optional[str] = None


@dataclass
class AccessLogConfig:
    log_url: str
    token_id: str
    wrap_pdf_links: bool = False


@dataclass
class DeliveryResult:
    report_id: str
    report_url: str
    pdf_url: str
    expires_at: str
    token_id: str
    link_manifest_path: Optional[Path] = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def detect_inline_data(report_html: Path) -> bool:
    content = report_html.read_text(encoding="utf-8", errors="ignore")
    markers = ["documentText", "documentMetadata", "__REPORT_DATA__"]
    return any(marker in content for marker in markers)


def externalize_report_data(bundle: ReportBundle) -> bool:
    data_path = bundle.base_dir / "report-data.json"
    if data_path.exists():
        return False

    html_text = bundle.report_html.read_text(encoding="utf-8", errors="ignore")
    match = REPORT_DATA_SCRIPT_RE.search(html_text)
    if not match:
        print("WARNING: report-data.json missing and no <script id=\"report-data\"> block found.")
        return False

    payload = match.group("content").strip()
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("report-data script tag content is not valid JSON") from exc

    data_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    updated_html = html_text[: match.start()] + REPORT_DATA_LOADER + html_text[match.end() :]
    bundle.report_html.write_text(updated_html, encoding="utf-8")
    return True


def collect_report_bundle(base_dir: Path, report_id: str) -> ReportBundle:
    if not base_dir.exists():
        raise FileNotFoundError(f"Bundle directory not found: {base_dir}")

    report_html = base_dir / "report.html"
    report_pdf = base_dir / "report.pdf"
    if not report_html.exists():
        raise FileNotFoundError(f"Missing report.html in {base_dir}")
    if not report_pdf.exists():
        raise FileNotFoundError(f"Missing report.pdf in {base_dir}")

    files: List[Path] = []
    for path in base_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name in SKIP_FILENAMES:
            continue
        files.append(path)

    return ReportBundle(
        base_dir=base_dir,
        report_id=report_id,
        report_html=report_html,
        report_pdf=report_pdf,
        files=sorted(files),
    )


def create_offline_zip(bundle: ReportBundle) -> Path:
    zip_path = bundle.base_dir / "report_offline.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in bundle.files:
            zf.write(path, arcname=bundle.relative_path(path))
    return zip_path


def build_s3_client(config: S3Config):
    if boto3 is None:
        raise RuntimeError("boto3 is required for S3 uploads. Install ops/report_delivery/requirements.txt")
    session = boto3.session.Session(region_name=config.region)
    return session.client("s3", endpoint_url=config.endpoint_url)


def detect_content_type(path: Path) -> str:
    mimetypes.add_type("application/pdf", ".pdf")
    mimetypes.add_type("application/json", ".json")
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("font/woff2", ".woff2")
    mimetypes.add_type("font/woff", ".woff")
    mimetypes.add_type("font/ttf", ".ttf")
    content_type, _ = mimetypes.guess_type(path.name)
    return content_type or "application/octet-stream"


def upload_bundle(
    s3_client,
    config: S3Config,
    bundle: ReportBundle,
    cache_control: str = "private, max-age=0, no-store",
) -> Dict[str, str]:
    key_map: Dict[str, str] = {}
    for path in bundle.files:
        rel_path = bundle.relative_path(path)
        key = f"{config.prefix.rstrip('/')}/{bundle.report_id}/{rel_path}"
        extra_args = {
            "ContentType": detect_content_type(path),
            "CacheControl": cache_control,
        }
        if path.suffix.lower() == ".pdf":
            extra_args["ContentDisposition"] = f'inline; filename="{path.name}"'
        s3_client.upload_file(str(path), config.bucket, key, ExtraArgs=extra_args)
        key_map[rel_path] = key
    return key_map


def generate_signed_urls(
    s3_client,
    config: S3Config,
    key_map: Dict[str, str],
    expires_in: int,
) -> Dict[str, str]:
    url_map: Dict[str, str] = {}
    for rel_path, key in key_map.items():
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": config.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        url_map[rel_path] = url
    return url_map


def _append_query(url: str, params: Dict[str, str]) -> str:
    parts = urlsplit(url)
    existing = dict([p.split("=", 1) for p in parts.query.split("&") if p])
    existing.update(params)
    new_query = urlencode(existing, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _is_relative_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    if lowered.startswith(("http://", "https://", "data:", "mailto:", "javascript:", "blob:")):
        return False
    if lowered.startswith("#"):
        return False
    return True


def _normalize_asset_path(path: str) -> str:
    if path.startswith("/"):
        path = path[1:]
    if path.startswith("./"):
        path = path[2:]
    return path


def _replace_url(url: str, url_map: Dict[str, str]) -> str:
    if not _is_relative_url(url):
        return url
    parts = urlsplit(url)
    normalized = _normalize_asset_path(parts.path)
    signed = url_map.get(normalized)
    if not signed:
        return url
    if parts.fragment:
        return f"{signed}#{parts.fragment}"
    return signed


def rewrite_html(html_text: str, url_map: Dict[str, str], access_log: Optional[AccessLogConfig]) -> str:
    attr_re = re.compile(r'(?P<attr>\b(?:src|href|data|poster)=)(?P<quote>["\'])(?P<url>[^"\']+)(?P=quote)')

    def _attr_replace(match: re.Match) -> str:
        url = match.group("url")
        replaced = _replace_url(url, url_map)
        if access_log and access_log.wrap_pdf_links and url.lower().endswith(".pdf"):
            replaced = wrap_url_for_log(replaced, access_log, event="download_pdf")
        return f"{match.group('attr')}{match.group('quote')}{replaced}{match.group('quote')}"

    html_text = html_text.replace("__REPORT_DATA_URL__", url_map.get("report-data.json", "report-data.json"))
    html_text = html_text.replace("__REPORT_PDF_URL__", url_map.get("report.pdf", "report.pdf"))
    html_text = attr_re.sub(_attr_replace, html_text)

    if access_log:
        html_text = inject_access_log_pixel(html_text, access_log)

    return html_text


def rewrite_css(css_text: str, url_map: Dict[str, str]) -> str:
    url_re = re.compile(r"url\((?P<quote>['\"]?)(?P<url>[^'\")]+)(?P=quote)\)")

    def _url_replace(match: re.Match) -> str:
        url = match.group("url")
        replaced = _replace_url(url, url_map)
        return f"url({match.group('quote')}{replaced}{match.group('quote')})"

    return url_re.sub(_url_replace, css_text)


def rewrite_js(js_text: str, url_map: Dict[str, str]) -> str:
    string_re = re.compile(r"(?P<quote>['\"])(?P<url>[^'\"]+)(?P=quote)")

    def _string_replace(match: re.Match) -> str:
        url = match.group("url")
        replaced = _replace_url(url, url_map)
        return f"{match.group('quote')}{replaced}{match.group('quote')}"

    return string_re.sub(_string_replace, js_text)


def rewrite_text_assets(
    bundle: ReportBundle,
    url_map: Dict[str, str],
    access_log: Optional[AccessLogConfig],
) -> List[Path]:
    updated_paths: List[Path] = []
    for path in bundle.files:
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        original = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".html":
            updated = rewrite_html(original, url_map, access_log)
        elif path.suffix.lower() == ".css":
            updated = rewrite_css(original, url_map)
        else:
            updated = rewrite_js(original, url_map)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            updated_paths.append(path)
    return updated_paths


def inject_access_log_pixel(html_text: str, access_log: AccessLogConfig) -> str:
    pixel_url = _append_query(
        access_log.log_url,
        {
            "report_id": access_log.token_id.split(":", 1)[0],
            "token_id": access_log.token_id,
            "event": "view",
        },
    )
    pixel_tag = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />'
    if "</body>" in html_text:
        return html_text.replace("</body>", f"{pixel_tag}\n</body>")
    return html_text + "\n" + pixel_tag


def wrap_url_for_log(url: str, access_log: AccessLogConfig, event: str) -> str:
    return _append_query(
        access_log.log_url,
        {
            "report_id": access_log.token_id.split(":", 1)[0],
            "token_id": access_log.token_id,
            "event": event,
            "redirect": url,
        },
    )


def build_email_body(
    report_url: str,
    pdf_url: str,
    expires_at: str,
    contact: Optional[str],
    attached: bool,
) -> Tuple[str, str]:
    expiry_line = f"Link expires: {expires_at} (UTC)"
    contact_line = f"Contact {contact} for reissue." if contact else "Contact the sender for reissue."
    attach_line = "PDF is attached." if attached else f"PDF link: {pdf_url}"
    text_body = "\n".join(
        [
            "Your report is ready.",
            "",
            f"Interactive report: {report_url}",
            attach_line,
            expiry_line,
            contact_line,
        ]
    )
    html_body = "".join(
        [
            "<p>Your report is ready.</p>",
            f"<p><a href=\"{report_url}\">Open interactive report</a></p>",
            "<p>"
            + ("PDF is attached." if attached else f"<a href=\"{pdf_url}\">Download PDF</a>")
            + "</p>",
            f"<p>{expiry_line}</p>",
            f"<p>{contact_line}</p>",
        ]
    )
    return text_body, html_body


def send_report_email(
    email_config: EmailConfig,
    report_url: str,
    pdf_url: str,
    expires_at: str,
    pdf_path: Path,
) -> None:
    attach_pdf = pdf_path.stat().st_size <= email_config.attach_max_bytes
    text_body, html_body = build_email_body(
        report_url,
        pdf_url,
        expires_at,
        email_config.contact,
        attached=attach_pdf,
    )

    msg = EmailMessage()
    msg["Subject"] = email_config.subject
    msg["From"] = email_config.sender
    msg["To"] = ", ".join(email_config.recipients)
    if email_config.reply_to:
        msg["Reply-To"] = email_config.reply_to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    if attach_pdf:
        msg.add_attachment(
            pdf_path.read_bytes(),
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )

    with smtplib.SMTP(email_config.smtp_host, email_config.smtp_port) as server:
        if email_config.use_tls:
            server.starttls()
        if email_config.smtp_username:
            server.login(email_config.smtp_username, email_config.smtp_password or "")
        server.send_message(msg)


def write_link_manifest(path: Path, result: DeliveryResult) -> None:
    payload = {
        "report_id": result.report_id,
        "report_url": result.report_url,
        "pdf_url": result.pdf_url,
        "expires_at": result.expires_at,
        "token_id": result.token_id,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def deliver_report(
    bundle_dir: Path,
    report_id: Optional[str],
    s3_config: S3Config,
    email_config: EmailConfig,
    expires_in: int,
    access_log_url: Optional[str] = None,
    wrap_pdf_links: bool = False,
    externalize_data: bool = False,
    create_zip: bool = False,
    write_manifest: bool = True,
) -> DeliveryResult:
    report_id = report_id or f"report-{utcnow().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}"
    bundle = collect_report_bundle(bundle_dir, report_id)

    if externalize_data:
        if externalize_report_data(bundle):
            bundle = collect_report_bundle(bundle_dir, report_id)

    if create_zip:
        create_offline_zip(bundle)

    if detect_inline_data(bundle.report_html):
        print("WARNING: report.html appears to include inline data. Consider externalizing to report-data.json.")

    s3_client = build_s3_client(s3_config)
    key_map = upload_bundle(s3_client, s3_config, bundle)

    url_map = generate_signed_urls(s3_client, s3_config, key_map, expires_in)
    token_id = f"{report_id}:{secrets.token_hex(6)}"

    access_log = None
    if access_log_url:
        access_log = AccessLogConfig(log_url=access_log_url, token_id=token_id, wrap_pdf_links=wrap_pdf_links)

    updated_paths = rewrite_text_assets(bundle, url_map, access_log)
    if updated_paths:
        upload_bundle(s3_client, s3_config, ReportBundle(bundle.base_dir, bundle.report_id, bundle.report_html, bundle.report_pdf, updated_paths))

    report_url = url_map[bundle.relative_path(bundle.report_html)]
    pdf_url = url_map[bundle.relative_path(bundle.report_pdf)]

    if access_log and wrap_pdf_links:
        pdf_url = wrap_url_for_log(pdf_url, access_log, event="download_pdf")

    expires_at = (utcnow() + timedelta(seconds=expires_in)).strftime("%Y-%m-%d %H:%M:%S")

    send_report_email(email_config, report_url, pdf_url, expires_at, bundle.report_pdf)

    result = DeliveryResult(
        report_id=report_id,
        report_url=report_url,
        pdf_url=pdf_url,
        expires_at=expires_at,
        token_id=token_id,
    )

    if write_manifest:
        manifest_path = bundle.base_dir / "hosted_links.json"
        write_link_manifest(manifest_path, result)
        result.link_manifest_path = manifest_path

    return result


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    return value if value else None


def load_config(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_email_config(raw: Dict[str, object]) -> EmailConfig:
    smtp = raw.get("smtp", {})
    password = smtp.get("password")
    password_env = smtp.get("password_env")
    if password_env:
        password = _get_env(str(password_env))

    recipients = raw.get("to", [])
    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(",") if r.strip()]

    return EmailConfig(
        sender=str(raw.get("from")),
        recipients=list(recipients),
        subject=str(raw.get("subject")),
        smtp_host=str(smtp.get("host")),
        smtp_port=int(smtp.get("port", 587)),
        smtp_username=smtp.get("username"),
        smtp_password=password,
        use_tls=bool(smtp.get("use_tls", True)),
        reply_to=raw.get("reply_to"),
        attach_max_bytes=int(raw.get("attach_max_bytes", 15_000_000)),
        contact=raw.get("contact"),
    )


def parse_s3_config(raw: Dict[str, object]) -> S3Config:
    return S3Config(
        bucket=str(raw.get("bucket")),
        prefix=str(raw.get("prefix", "reports")),
        region=raw.get("region"),
        endpoint_url=raw.get("endpoint_url"),
    )


def deliver_from_config(config: Dict[str, object]) -> DeliveryResult:
    bundle_dir = Path(str(config.get("bundle_dir")))
    report_id = config.get("report_id")
    expires_in = int(config.get("expires_in", 60 * 60 * 24 * 7))
    access_log = config.get("access_log") or {}

    s3_config = parse_s3_config(config.get("s3", {}))
    email_config = parse_email_config(config.get("email", {}))

    return deliver_report(
        bundle_dir=bundle_dir,
        report_id=str(report_id) if report_id else None,
        s3_config=s3_config,
        email_config=email_config,
        expires_in=expires_in,
        access_log_url=access_log.get("log_url"),
        wrap_pdf_links=bool(access_log.get("wrap_pdf_links", False)),
        externalize_data=bool(config.get("externalize_data", False)),
        create_zip=bool(config.get("create_offline_zip", False)),
        write_manifest=bool(config.get("write_manifest", True)),
    )


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: report_delivery.py /path/to/config.json")
        return 2
    config_path = Path(argv[0])
    result = deliver_from_config(load_config(config_path))
    print(f"Report delivered: {result.report_url}")
    if result.link_manifest_path:
        print(f"Manifest: {result.link_manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
