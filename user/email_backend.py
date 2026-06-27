"""
自定义邮件后端，用于在开发环境中禁用SSL证书验证
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class CustomEmailBackend(SMTPBackend):
    """自定义邮件后端，禁用SSL证书验证（仅用于开发环境）"""
    
    def open(self):
        """重写open方法，禁用SSL证书验证"""
        if self.connection:
            return False
        
        try:
            # 如果使用SSL，创建不验证证书的SSL上下文
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.connection = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout,
                    context=context
                )
            else:
                self.connection = self.connection_class(
                    self.host,
                    self.port,
                    timeout=self.timeout,
                )
                
                # 如果使用TLS，启动TLS但不验证证书
                if self.use_tls:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    self.connection.starttls(context=context)
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            
            return True
        except Exception:
            if not self.fail_silently:
                raise

