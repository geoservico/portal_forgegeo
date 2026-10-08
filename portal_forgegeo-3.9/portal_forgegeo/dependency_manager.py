import importlib
import os
import platform
import re
import site
import subprocess  # nosec B404
import sys

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import Qgis, QgsMessageLog


_PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def get_python_executable():
    """Retorna um executável Python confiável para o ambiente atual."""
    executable = os.path.abspath(sys.executable)
    if platform.system() == "Windows":
        bin_dir = os.path.dirname(executable)
        possible_pythons = [
            os.path.join(bin_dir, "python.exe"),
            os.path.join(bin_dir, "python3.exe"),
            os.path.abspath(os.path.join(bin_dir, "..", "bin", "python.exe")),
            os.path.abspath(os.path.join(bin_dir, "..", "apps", "Python39", "python.exe")),
            os.path.abspath(os.path.join(bin_dir, "..", "apps", "Python310", "python.exe")),
            os.path.abspath(os.path.join(bin_dir, "..", "apps", "Python311", "python.exe")),
        ]
        for candidate in possible_pythons:
            if os.path.isfile(candidate):
                return candidate
    return executable


def update_python_path():
    """Atualiza o sys.path após a instalação de pacotes."""
    importlib.reload(site)
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            py_ver = f"{sys.version_info.major}{sys.version_info.minor}"
            user_site = os.path.join(appdata, "Python", f"Python{py_ver}", "site-packages")
            if os.path.isdir(user_site) and user_site not in sys.path:
                sys.path.append(user_site)
                QgsMessageLog.logMessage(
                    f"Caminho de usuário adicionado: {user_site}",
                    "PortalForgegeo",
                    Qgis.MessageLevel.Info,
                )


def _validate_package_name(package_name):
    """Aceita somente nomes de pacote, nunca opções ou comandos de shell."""
    if not isinstance(package_name, str) or not _PACKAGE_NAME_RE.fullmatch(package_name):
        raise ValueError(f"Nome de pacote inválido: {package_name!r}")


def _run_pip(python_executable, package_name, user=False):
    """Executa pip sem shell e com argumentos separados."""
    _validate_package_name(package_name)
    command = [python_executable, "-m", "pip", "install", "--upgrade"]
    if user:
        command.append("--user")
    command.append(package_name)
    # nosec B603
    return subprocess.run(
        command,
        check=False,
        shell=False,  # nosec B603
        capture_output=True,
        text=True,
        timeout=600,
    )


def install_dependencies(requirements_list):
    """Instala dependências ausentes sem interpretar entradas como comandos."""
    missing_packages = []
    for package_name, import_name in requirements_list:
        try:
            importlib.import_module(import_name)
        except (ImportError, AttributeError, NameError):
            missing_packages.append((package_name, import_name))

    if not missing_packages:
        return True

    names = "\n".join(package for package, _ in missing_packages)
    msg = (
        "O plugin Portal Forgegeo precisa instalar/atualizar as seguintes "
        f"dependências Python:\n\n{names}\n\nIsso pode levar alguns instantes. Deseja prosseguir?"
    )
    reply = QMessageBox.question(
        None,
        "Instalação de Dependências",
        msg,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if reply == QMessageBox.StandardButton.No:
        return False

    success = True
    python_executable = get_python_executable()
    for package_name, import_name in missing_packages:
        QgsMessageLog.logMessage(
            f"Instalando/Atualizando {package_name}...", "PortalForgegeo", Qgis.MessageLevel.Info
        )
        try:
            result = _run_pip(python_executable, package_name)
            if result.returncode != 0 and platform.system() == "Windows":
                QgsMessageLog.logMessage(
                    f"Tentando {package_name} com --user...", "PortalForgegeo", Qgis.MessageLevel.Info
                )
                result = _run_pip(python_executable, package_name, user=True)

            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "sem detalhes").strip()
                QgsMessageLog.logMessage(
                    f"Falha ao instalar {package_name}: {detail}",
                    "PortalForgegeo",
                    Qgis.MessageLevel.Critical,
                )
                success = False
                continue

            update_python_path()
            try:
                importlib.import_module(import_name)
                QgsMessageLog.logMessage(
                    f"Sucesso ao validar {package_name}", "PortalForgegeo", Qgis.MessageLevel.Success
                )
            except (ImportError, AttributeError, NameError) as import_error:
                QgsMessageLog.logMessage(
                    f"Falha ao validar {package_name} após instalação: {import_error}",
                    "PortalForgegeo",
                    Qgis.MessageLevel.Critical,
                )
                success = False
        except (OSError, subprocess.SubprocessError, ValueError) as install_error:
            QgsMessageLog.logMessage(
                f"Erro na instalação de {package_name}: {install_error}",
                "PortalForgegeo",
                Qgis.MessageLevel.Critical,
            )
            success = False

    if success:
        QMessageBox.information(
            None, "Sucesso", "Dependências instaladas com sucesso. Seja bem-vindo ao GeoNexus."
        )
    else:
        QMessageBox.critical(
            None,
            "Erro",
            "Não foi possível validar algumas dependências. Tente reiniciar o QGIS.",
        )
    return success
