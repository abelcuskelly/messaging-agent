"""
Automated Reporting and Scheduled Exports
Generate and schedule reports automatically
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
from enum import Enum
import json
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import structlog

logger = structlog.get_logger()


class ReportFrequency(str, Enum):
    """Report frequency options"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportFormat(str, Enum):
    """Report export formats"""
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    HTML = "html"
    JSON = "json"


class ReportConfig(BaseModel):
    """Report configuration"""
    id: str
    name: str
    description: Optional[str] = None
    frequency: ReportFrequency
    format: ReportFormat
    recipients: List[EmailStr]
    include_charts: bool = True
    include_tables: bool = True
    metrics: List[str] = Field(description="Metrics to include in report")
    filters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class ReportManager:
    """Manage automated reports"""
    
    def __init__(self, redis_client, bigquery_client=None):
        self.redis = redis_client
        self.bigquery = bigquery_client
        self.logger = logger
        
        # Email configuration
        self.smtp_host = "smtp.gmail.com"  # Configure based on provider
        self.smtp_port = 587
        self.smtp_user = None  # Set from environment
        self.smtp_password = None  # Set from environment
    
    async def create_report(self, report: ReportConfig) -> Dict[str, Any]:
        """Create a new scheduled report"""
        try:
            # Calculate next run time
            report.next_run = self._calculate_next_run(report.frequency)
            
            report_key = f"report:{report.id}"
            await self.redis.hset(
                report_key,
                mapping={
                    "name": report.name,
                    "description": report.description or "",
                    "frequency": report.frequency.value,
                    "format": report.format.value,
                    "recipients": json.dumps(report.recipients),
                    "include_charts": str(report.include_charts),
                    "include_tables": str(report.include_tables),
                    "metrics": json.dumps(report.metrics),
                    "filters": json.dumps(report.filters),
                    "enabled": str(report.enabled),
                    "created_at": report.created_at.isoformat(),
                    "next_run": report.next_run.isoformat()
                }
            )
            
            # Add to scheduled reports
            if report.enabled:
                await self.redis.zadd(
                    "reports:scheduled",
                    {report.id: report.next_run.timestamp()}
                )
            
            self.logger.info("Report created", report_id=report.id, frequency=report.frequency)
            
            return {"status": "success", "report_id": report.id, "next_run": report.next_run}
            
        except Exception as e:
            self.logger.error("Failed to create report", error=str(e))
            raise
    
    async def generate_report(self, report_id: str) -> Dict[str, Any]:
        """Generate a report on demand"""
        try:
            report = await self.get_report(report_id)
            
            if not report:
                return {"status": "error", "message": "Report not found"}
            
            # Collect data for report
            data = await self._collect_report_data(report)
            
            # Generate report in requested format
            report_file = await self._format_report(report, data)
            
            # Send to recipients
            if report.recipients:
                await self._send_report_email(report, report_file)
            
            # Update last run time
            await self.redis.hset(f"report:{report_id}", "last_run", datetime.now().isoformat())
            
            # Schedule next run
            next_run = self._calculate_next_run(report.frequency)
            await self.redis.hset(f"report:{report_id}", "next_run", next_run.isoformat())
            await self.redis.zadd("reports:scheduled", {report_id: next_run.timestamp()})
            
            self.logger.info("Report generated", report_id=report_id)
            
            return {
                "status": "success",
                "report_id": report_id,
                "format": report.format.value,
                "recipients": len(report.recipients),
                "next_run": next_run
            }
            
        except Exception as e:
            self.logger.error("Failed to generate report", report_id=report_id, error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def get_report(self, report_id: str) -> Optional[ReportConfig]:
        """Get report configuration"""
        try:
            report_data = await self.redis.hgetall(f"report:{report_id}")
            
            if not report_data:
                return None
            
            return ReportConfig(
                id=report_id,
                name=report_data["name"],
                description=report_data.get("description"),
                frequency=ReportFrequency(report_data["frequency"]),
                format=ReportFormat(report_data["format"]),
                recipients=json.loads(report_data["recipients"]),
                include_charts=report_data.get("include_charts") == "True",
                include_tables=report_data.get("include_tables") == "True",
                metrics=json.loads(report_data["metrics"]),
                filters=json.loads(report_data.get("filters", "{}")),
                enabled=report_data.get("enabled") == "True",
                created_at=datetime.fromisoformat(report_data["created_at"]),
                last_run=datetime.fromisoformat(report_data["last_run"]) if report_data.get("last_run") else None,
                next_run=datetime.fromisoformat(report_data["next_run"]) if report_data.get("next_run") else None
            )
            
        except Exception as e:
            self.logger.error("Failed to get report", report_id=report_id, error=str(e))
            return None
    
    async def list_reports(self) -> List[Dict[str, Any]]:
        """List all reports"""
        try:
            report_keys = await self.redis.keys("report:*")
            
            reports = []
            for key in report_keys:
                report_id = key.split(":")[-1]
                report = await self.get_report(report_id)
                if report:
                    reports.append({
                        "id": report.id,
                        "name": report.name,
                        "frequency": report.frequency.value,
                        "format": report.format.value,
                        "enabled": report.enabled,
                        "last_run": report.last_run.isoformat() if report.last_run else None,
                        "next_run": report.next_run.isoformat() if report.next_run else None
                    })
            
            return reports
            
        except Exception as e:
            self.logger.error("Failed to list reports", error=str(e))
            return []
    
    async def _collect_report_data(self, report: ReportConfig) -> Dict[str, Any]:
        """Collect data for report generation"""
        data = {}
        
        # Get metrics data
        for metric in report.metrics:
            if metric == "conversations":
                data["conversations"] = await self._get_conversation_metrics()
            elif metric == "users":
                data["users"] = await self._get_user_metrics()
            elif metric == "performance":
                data["performance"] = await self._get_performance_metrics()
            elif metric == "billing":
                data["billing"] = await self._get_billing_metrics()
            elif metric == "errors":
                data["errors"] = await self._get_error_metrics()
        
        return data
    
    async def _get_conversation_metrics(self) -> Dict[str, Any]:
        """Get conversation metrics"""
        total = await self.redis.get("metrics:total_conversations") or 0
        active = await self.redis.get("metrics:active_conversations") or 0
        
        # Get daily conversation counts for the period
        daily_counts = []
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            count = await self.redis.get(f"metrics:daily:{date.date()}:conversations") or 0
            daily_counts.append({"date": date.date().isoformat(), "count": int(count)})
        
        return {
            "total": int(total),
            "active": int(active),
            "daily_counts": daily_counts
        }
    
    async def _get_user_metrics(self) -> Dict[str, Any]:
        """Get user metrics"""
        active_users = await self.redis.scard("metrics:active_users") or 0
        
        return {
            "active_users": int(active_users)
        }
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        avg_response = await self.redis.get("metrics:avg_response_time") or 0
        success_rate = await self.redis.get("metrics:success_rate") or 0
        
        return {
            "avg_response_time": float(avg_response),
            "success_rate": float(success_rate)
        }
    
    async def _get_billing_metrics(self) -> Dict[str, Any]:
        """Get billing metrics"""
        current_month = datetime.now().strftime("%Y-%m")
        api_calls = await self.redis.get(f"usage:{current_month}:api_calls") or 0
        tokens = await self.redis.get(f"usage:{current_month}:tokens") or 0
        
        cost = int(api_calls) * 0.0001 + int(tokens) * 0.000002
        
        return {
            "api_calls": int(api_calls),
            "tokens": int(tokens),
            "estimated_cost": cost
        }
    
    async def _get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics"""
        error_count = await self.redis.get("metrics:errors") or 0
        
        return {
            "total_errors": int(error_count)
        }
    
    async def _format_report(self, report: ReportConfig, data: Dict[str, Any]) -> bytes:
        """Format report based on requested format"""
        if report.format == ReportFormat.CSV:
            return await self._generate_csv(data)
        elif report.format == ReportFormat.EXCEL:
            return await self._generate_excel(data)
        elif report.format == ReportFormat.HTML:
            return await self._generate_html(report, data)
        elif report.format == ReportFormat.JSON:
            return json.dumps(data, indent=2, default=str).encode()
        elif report.format == ReportFormat.PDF:
            return await self._generate_pdf(report, data)
        
        return b""
    
    async def _generate_csv(self, data: Dict[str, Any]) -> bytes:
        """Generate CSV report"""
        # Flatten data for CSV
        rows = []
        
        if "conversations" in data:
            for item in data["conversations"]["daily_counts"]:
                rows.append({
                    "date": item["date"],
                    "conversations": item["count"]
                })
        
        df = pd.DataFrame(rows)
        return df.to_csv(index=False).encode()
    
    async def _generate_excel(self, data: Dict[str, Any]) -> bytes:
        """Generate Excel report"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Conversations sheet
            if "conversations" in data:
                df = pd.DataFrame(data["conversations"]["daily_counts"])
                df.to_excel(writer, sheet_name='Conversations', index=False)
            
            # Performance sheet
            if "performance" in data:
                df = pd.DataFrame([data["performance"]])
                df.to_excel(writer, sheet_name='Performance', index=False)
            
            # Billing sheet
            if "billing" in data:
                df = pd.DataFrame([data["billing"]])
                df.to_excel(writer, sheet_name='Billing', index=False)
        
        return output.getvalue()
    
    async def _generate_html(self, report: ReportConfig, data: Dict[str, Any]) -> bytes:
        """Generate HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .metric {{ background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 5px; }}
                .metric-value {{ font-size: 32px; font-weight: bold; color: #4CAF50; }}
            </style>
        </head>
        <body>
            <h1>{report.name}</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        # Add metrics
        if "conversations" in data:
            html += f"""
            <h2>Conversations</h2>
            <div class="metric">
                <div>Total Conversations</div>
                <div class="metric-value">{data['conversations']['total']}</div>
            </div>
            """
        
        if "performance" in data:
            html += f"""
            <h2>Performance</h2>
            <div class="metric">
                <div>Average Response Time</div>
                <div class="metric-value">{data['performance']['avg_response_time']:.0f}ms</div>
            </div>
            <div class="metric">
                <div>Success Rate</div>
                <div class="metric-value">{data['performance']['success_rate']:.1f}%</div>
            </div>
            """
        
        if "billing" in data:
            html += f"""
            <h2>Billing</h2>
            <div class="metric">
                <div>API Calls</div>
                <div class="metric-value">{data['billing']['api_calls']:,}</div>
            </div>
            <div class="metric">
                <div>Estimated Cost</div>
                <div class="metric-value">${data['billing']['estimated_cost']:.2f}</div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html.encode()
    
    async def _generate_pdf(self, report: ReportConfig, data: Dict[str, Any]) -> bytes:
        """Generate PDF report (requires reportlab)"""
        # For now, return HTML (can be converted to PDF with external tools)
        return await self._generate_html(report, data)
    
    async def _send_report_email(self, report: ReportConfig, report_file: bytes):
        """Send report via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(report.recipients)
            msg['Subject'] = f"{report.name} - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Email body
            body = f"""
            Your automated report is ready!
            
            Report: {report.name}
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Format: {report.format.value}
            
            Please find the report attached.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report file
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(report_file)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{report.name}.{report.format.value}"'
            )
            msg.attach(attachment)
            
            # Send email
            if self.smtp_user and self.smtp_password:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                
                self.logger.info("Report email sent", report_id=report.id, recipients=len(report.recipients))
            else:
                self.logger.warning("SMTP credentials not configured, email not sent")
            
        except Exception as e:
            self.logger.error("Failed to send report email", error=str(e))
    
    def _calculate_next_run(self, frequency: ReportFrequency) -> datetime:
        """Calculate next run time based on frequency"""
        now = datetime.now()
        
        if frequency == ReportFrequency.HOURLY:
            return now + timedelta(hours=1)
        elif frequency == ReportFrequency.DAILY:
            # Next day at 9 AM
            next_run = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            return next_run
        elif frequency == ReportFrequency.WEEKLY:
            # Next Monday at 9 AM
            days_until_monday = (7 - now.weekday()) % 7 or 7
            next_run = (now + timedelta(days=days_until_monday)).replace(hour=9, minute=0, second=0, microsecond=0)
            return next_run
        elif frequency == ReportFrequency.MONTHLY:
            # First day of next month at 9 AM
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1, hour=9, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=1, hour=9, minute=0, second=0, microsecond=0)
            return next_run
        
        return now + timedelta(days=1)
    
    async def process_scheduled_reports(self):
        """Process all scheduled reports that are due"""
        try:
            # Get reports due for execution
            now = datetime.now().timestamp()
            due_reports = await self.redis.zrangebyscore("reports:scheduled", "-inf", now)
            
            for report_id in due_reports:
                self.logger.info("Processing scheduled report", report_id=report_id)
                await self.generate_report(report_id)
                
        except Exception as e:
            self.logger.error("Failed to process scheduled reports", error=str(e))
