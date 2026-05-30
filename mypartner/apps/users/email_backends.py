import ssl

from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.utils import DNS_NAME


class TLS13EmailBackend(SMTPBackend):
    """SMTP backend que negocia STARTTLS exigiendo TLS 1.3 como mínimo."""

    def open(self):
        if self.connection:
            return False

        connection_params = {'local_hostname': DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            connection_params['keyfile'] = self.ssl_keyfile
            connection_params['certfile'] = self.ssl_certfile

        try:
            self.connection = self.connection_class(self.host, self.port, **connection_params)
            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                context = ssl.create_default_context()
                context.minimum_version = ssl.TLSVersion.TLSv1_3
                self.connection.starttls(context=context)
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
