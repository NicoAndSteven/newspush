"""
邮箱推送工具 - 将生成的新闻文章发送到指定邮箱
支持发送Markdown和Word文档附件
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime


class EmailSender:
    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None
    ):
        from config import config
        self.smtp_server = smtp_server or config.SMTP_SERVER
        self.smtp_port = smtp_port or config.SMTP_PORT
        self.smtp_user = smtp_user or config.SMTP_USER
        self.smtp_password = smtp_password or config.SMTP_PASSWORD
    
    def is_configured(self) -> bool:
        """检查是否配置了邮箱"""
        return bool(self.smtp_user and self.smtp_password)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: List[str] = None,
        body_html: str = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文（纯文本）
            attachments: 附件文件路径列表
            body_html: HTML格式正文（可选）
        
        Returns:
            是否发送成功
        """
        if not self.is_configured():
            print("[Email] 邮箱未配置，跳过发送")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if body_html:
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        print(f"[Email] 附件不存在: {file_path}")
                        continue
                    
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(file_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename*=UTF-8\'\'{filename}'
                        )
                        msg.attach(part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())
            
            print(f"[Email] 邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"[Email] 发送失败: {e}")
            return False
    
    def send_news_digest(
        self,
        to_email: str,
        articles: List[Dict],
        attachments: List[str] = None
    ) -> bool:
        """
        发送新闻摘要邮件
        
        Args:
            to_email: 收件人邮箱
            articles: 文章列表，每篇包含 title, summary, file_path
            attachments: 附件文件路径列表
        """
        today = datetime.now().strftime("%Y年%m月%d日")
        subject = f"📰 今日新闻点评 - {today}"
        
        body_lines = [f"今日新闻点评 ({today})", "=" * 40, ""]
        
        for i, article in enumerate(articles, 1):
            body_lines.append(f"【{i}】{article.get('title', '未知标题')}")
            if article.get('summary'):
                body_lines.append(f"   {article['summary'][:100]}...")
            body_lines.append("")
        
        body_lines.append("-" * 40)
        body_lines.append("详细内容请查看附件或访问原文链接。")
        body_lines.append("")
        body_lines.append("此邮件由 NewsPush 自动生成")
        
        body = "\n".join(body_lines)
        
        html_lines = [
            f"<h2>📰 今日新闻点评 - {today}</h2>",
            "<hr>",
            "<ul>"
        ]
        
        for article in articles:
            title = article.get('title', '未知标题')
            summary = article.get('summary', '')[:150]
            html_lines.append(f"<li><b>{title}</b><br><small>{summary}...</small></li>")
        
        html_lines.append("</ul>")
        html_lines.append("<hr>")
        html_lines.append("<p><small>此邮件由 NewsPush 自动生成</small></p>")
        
        body_html = "\n".join(html_lines)
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=attachments,
            body_html=body_html
        )


def send_results_via_email(
    results_dir: str = "./results",
    to_email: str = None,
    max_files: int = 5
) -> bool:
    """
    发送results目录中的最新文章到邮箱
    
    Args:
        results_dir: 结果目录
        to_email: 收件人邮箱（None则使用配置）
        max_files: 最多发送多少个文件
    """
    from config import config
    
    sender = EmailSender()
    
    if not sender.is_configured():
        print("[Email] 邮箱未配置，跳过发送")
        return False
    
    to_email = to_email or config.EMAIL_TO
    if not to_email:
        print("[Email] 未配置收件人邮箱，跳过发送")
        return False
    
    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"[Email] 结果目录不存在: {results_dir}")
        return False
    
    md_files = sorted(
        results_path.glob("commentary_*_public.md"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:max_files]
    
    docx_files = sorted(
        results_path.glob("commentary_*_public.docx"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:max_files]
    
    if not md_files and not docx_files:
        print("[Email] 没有找到可发送的文章")
        return False
    
    articles = []
    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        title = lines[0].replace('# ', '') if lines else md_file.stem
        summary = '\n'.join(lines[1:5]) if len(lines) > 1 else ''
        articles.append({
            'title': title,
            'summary': summary,
            'file_path': str(md_file)
        })
    
    attachments = [str(f) for f in docx_files] if docx_files else [str(f) for f in md_files]
    
    return sender.send_news_digest(
        to_email=to_email,
        articles=articles,
        attachments=attachments
    )


if __name__ == "__main__":
    send_results_via_email()
