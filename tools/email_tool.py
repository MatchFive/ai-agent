"""
邮件发送工具
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Union

from pydantic import BaseModel, EmailStr, Field

from core.config import settings
from core.logger import logger


class EmailContent(BaseModel):
    """邮件内容"""
    to: Union[str, List[str]] = Field(..., description="收件人")
    subject: str = Field(..., description="邮件主题")
    body: str = Field(..., description="邮件正文")
    cc: Optional[List[str]] = Field(default=None, description="抄送")
    bcc: Optional[List[str]] = Field(default=None, description="密送")
    attachments: Optional[List[str]] = Field(default=None, description="附件路径")
    html: bool = Field(default=False, description="是否HTML格式")


class EmailTool:
    """
    邮件发送工具
    支持普通文本和HTML邮件，支持附件
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_addr: Optional[str] = None,
        use_tls: Optional[bool] = None,
    ):
        self.smtp_host = smtp_host or settings.email.smtp_host
        self.smtp_port = smtp_port or settings.email.smtp_port
        self.username = username or settings.email.username
        self.password = password or settings.email.password
        self.from_addr = from_addr or settings.email.from_addr or self.username
        self.use_tls = use_tls if use_tls is not None else settings.email.use_tls

    def _create_message(self, content: EmailContent) -> MIMEMultipart:
        """创建邮件消息"""
        msg = MIMEMultipart()
        msg['From'] = self.from_addr
        msg['To'] = ', '.join(content.to) if isinstance(content.to, list) else content.to
        msg['Subject'] = content.subject

        if content.cc:
            msg['Cc'] = ', '.join(content.cc)
        if content.bcc:
            msg['Bcc'] = ', '.join(content.bcc)

        # 添加正文
        body_part = MIMEText(
            content.body,
            'html' if content.html else 'plain',
            'utf-8'
        )
        msg.attach(body_part)

        # 添加附件
        if content.attachments:
            for attachment_path in content.attachments:
                self._attach_file(msg, attachment_path)

        return msg

    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> bool:
        """添加附件"""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Attachment not found: {file_path}")
            return False

        try:
            with open(path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{path.name}"'
                )
                msg.attach(part)
                logger.debug(f"Attached file: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {e}")
            return False

    def send(self, content: EmailContent) -> dict:
        """
        发送邮件

        Args:
            content: 邮件内容

        Returns:
            发送结果
        """
        try:
            msg = self._create_message(content)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.username and self.password:
                    server.login(self.username, self.password)

                recipients = [content.to] if isinstance(content.to, str) else content.to
                if content.cc:
                    recipients.extend(content.cc)
                if content.bcc:
                    recipients.extend(content.bcc)

                server.sendmail(self.from_addr, recipients, msg.as_string())

            logger.info(f"Email sent to {content.to}")
            return {
                "success": True,
                "message": f"Email sent successfully to {content.to}"
            }

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_async(self, content: EmailContent) -> dict:
        """异步发送邮件（当前为同步包装）"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send, content)

    # 便捷方法
    def send_text(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        **kwargs
    ) -> dict:
        """发送纯文本邮件"""
        return self.send(EmailContent(
            to=to,
            subject=subject,
            body=body,
            html=False,
            **kwargs
        ))

    def send_html(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        **kwargs
    ) -> dict:
        """发送HTML邮件"""
        return self.send(EmailContent(
            to=to,
            subject=subject,
            body=body,
            html=True,
            **kwargs
        ))
