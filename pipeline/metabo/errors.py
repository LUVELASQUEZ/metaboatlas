"""Errores del pipeline. Los mensajes van en español porque los leen las personas."""


class PipelineError(Exception):
    """Clase base de todos los errores del pipeline."""


class ConfigError(PipelineError):
    """Un archivo de configuración falta o no es válido."""


class SourceNotAllowedError(PipelineError):
    """Una fuente no se puede descargar (desconocida, solo enlace o sin verificar)."""


class DownloadError(PipelineError):
    """Una descarga falló después de los reintentos permitidos."""
