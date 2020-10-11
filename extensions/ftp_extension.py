# -*- coding: utf-*-
# SFTP and FTP uploader

from extension import Extension, NetExtensionConfig

DEFAULT_FTP_PORT: int = 21
DEFAULT_SFTP_PORT: int = 22


class FtpUploader(Extension):
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
                'FTP_SERVER or FTP_PORT not specified in configuration, skipping uploading')
            return False
        return True
