# -*- coding: utf-*-
# SFTP and FTP uploader

from extension import Extension, NetExtensionConfig

DEFAULT_FTP_PORT: int = 21
DEFAULT_SFTP_PORT: int = 22


class FtpUploader(Extension):
    @classmethod
    def new_config_instance(cls) -> NetExtensionConfig:
        """
        Instantiate a new configuration object for this type of extension.
        :return: a new configuration object
        """
        return NetExtensionConfig(cls.__name__)

    def __init__(self, config: NetExtensionConfig):
        """
        Set the configuration for the extension and initialize the list of pending images.
        :param config: the configuration
        """
        super().__init__(config)
        self._pending_images = list()

    def _add_pending(self, images: list, message=None) -> None:
        """
        Add images and optional message to pending elements to process
        :param images: the images to add for a later processing
        :param message: the message (not used by this extension)
        """
        self._pending_images.append(images)

    def _process(self, images: list, message=None) -> bool:
        """
        Transfer images to the FTP server.
        :param images: the images to transfer
        :param message: the message (not used by this extension)
        """
        # noinspection PyUnresolvedReferences
        if not self._config.get_server() or not self._config.get_port():
            self._get_logger().warning(
                'FTP_SERVER or FTP_PORT not specified in configuration, skipping uploading')
            return False
        return True
