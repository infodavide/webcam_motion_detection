# -*- coding: utf-*-
# SMTP notifier
import os
import smtplib
import zipstream
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from extension import Extension, NetExtensionConfig

DEFAULT_SMTP_PORT: int = 25


class SmtpNotifier(Extension):
    @classmethod
    def new_config_instance(cls) -> NetExtensionConfig:
        return NetExtensionConfig(cls.__name__)

    def __init__(self, config: NetExtensionConfig):
        super().__init__(config)
        self._pending_images = list()

    def _add_pending(self, images: list, message=None) -> None:
        self._pending_images.append(images)

    def _process(self, images: list, message=None) -> bool:
        # noinspection PyUnresolvedReferences
        if not self._config.get_server() or not self._config.get_port():
            self._get_logger().warning(
                'SMTP_SERVER or SMTP_PORT not specified in configuration, skipping email notification')
            return False
        # noinspection PyUnresolvedReferences
        if not self._config.get('from') or not self._config.get('to'):
            self._get_logger().warning('No from or to email address specified, skipping email notification')
            return False
        self._pending_images.append(images)
        parts = []
        for image in self._pending_images:
            part: MIMEApplication = MIMEApplication(
                image.data,
                Name=image.basename
            )
            part['Content-Disposition'] = 'attachment; filename="%s"' % image.basename
            parts.append(part)
        if len(parts) == 0:
            return False
        # noinspection PyUnresolvedReferences
        self._get_logger().info('Sending email to ' + self._config.get('to'))
        # noinspection PyTypeChecker
        server: smtplib.SMTP = None
        try:
            # noinspection PyUnresolvedReferences
            server = smtplib.SMTP(self._config.get_server(), self._config.get_port())
            msg: MIMEMultipart = MIMEMultipart()
            # noinspection PyUnresolvedReferences
            msg['From'] = self._config.get('from')
            # noinspection PyUnresolvedReferences
            msg['To'] = self._config.get('to')
            if message is None:
                mt = MIMEText(os.path.splitext(os.path.basename(__file__))[0] + ' completed', 'plain')
                mt['Subject'] = os.path.splitext(os.path.basename(__file__))[0] + ' completed'
            else:
                self._get_logger().debug(message)
                mt = MIMEText(os.path.splitext(os.path.basename(__file__))[
                                  0] + ' completed with error(s): ' + message + ', check logs', 'plain')
                mt['Subject'] = os.path.splitext(os.path.basename(__file__))[0] + ' completed with error(s)'
            msg['Subject'] = mt['Subject']
            # noinspection PyUnresolvedReferences
            mt['From'] = self._config.get('from')
            # noinspection PyUnresolvedReferences
            mt['To'] = self._config.get('to')
            msg.attach(mt)
            log_file_path: str = self._config.get('log_file_path')
            if log_file_path is not None:
                basename: str = os.path.basename(log_file_path + '.zip')
                zipfile = zipstream.ZipFile()
                zipfile.write(log_file_path, os.path.basename(log_file_path))
                # noinspection PyTypeChecker
                part = None
                for data in zipfile:
                    part = MIMEApplication(
                        data,
                        Name=basename
                    )
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename
                msg.attach(part)
            for part in parts:
                msg.attach(part)
            server.sendmail(msg['From'], self._config.get('to'), msg.as_string())
            self._pending_images.clear()
        finally:
            if server:
                server.close()
        return True
