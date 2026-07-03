# -*- coding: utf-8 -*-
import subprocess
import sys
import importlib
import os
import platform
import tempfile
import site

from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtWidgets import QMessageBox

def get_python_executable():
    """
    Tenta encontrar o executável real do Python no Windows/QGIS.
    """
    executable = sys.executable
    if platform.system() == "Windows":
        bin_dir = os.path.dirname(executable)
        possible_pythons = [
            os.path.join(bin_dir, "python.exe"),
            os.path.join(bin_dir, "python3.exe"),
            os.path.join(bin_dir, "..", "bin", "python.exe"),
            os.path.join(bin_dir, "..", "apps", "Python39", "python.exe"),
            os.path.join(bin_dir, "..", "apps", "Python310", "python.exe"),
            os.path.join(bin_dir, "..", "apps", "Python311", "python.exe"),
            os.path.join(os.environ.get("PYTHONHOME", ""), "python.exe")
        ]
        for py in possible_pythons:
            if os.path.exists(py):
                return py
    return executable

def update_python_path():
    """
    Força a atualização do sys.path para incluir diretórios de pacotes recém-instalados.
    """
    # Recarrega as pastas de site-packages
    importlib.reload(site)
    
    # No Windows/QGIS, pacotes --user costumam ir para %APPDATA%\Python\PythonXX\site-packages
    if platform.system() == "Windows":
        appdata = os.environ.get('APPDATA')
        if appdata:
            py_ver = f"{sys.version_info.major}{sys.version_info.minor}"
            user_site = os.path.join(appdata, "Python", f"Python{py_ver}", "site-packages")
            if os.path.exists(user_site) and user_site not in sys.path:
                sys.path.append(user_site)
                QgsMessageLog.logMessage(f"Caminho de usuário adicionado: {user_site}", "PortalForgegeo", Qgis.Info)

def install_dependencies(requirements_list):
    """
    Tenta instalar as dependências via pip se elas não estiverem presentes.
    """
    missing_packages = []
    for package_name, import_name in requirements_list:
        try:
            importlib.import_module(import_name)
        except (ImportError, AttributeError, NameError):
            missing_packages.append((package_name, import_name))
    
    if not missing_packages:
        return True

    msg = "O plugin Portal Forgegeo precisa instalar/atualizar as seguintes dependências Python: \n\n"
    msg += "\n".join([p[0] for p in missing_packages])
    msg += "\n\nIsso pode levar alguns instantes. Deseja prosseguir?"
    
    reply = QMessageBox.question(None, "Instalação de Dependências", msg, 
                                 QMessageBox.Yes | QMessageBox.No)
    
    if reply == QMessageBox.No:
        return False

    success = True
    python_exe = get_python_executable()
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    for package_name, import_name in missing_packages:
        QgsMessageLog.logMessage(f"Instalando/Atualizando {package_name}...", "PortalForgegeo", Qgis.Info)
        try:
            if platform.system() == "Windows":
                temp_dir = tempfile.gettempdir()
                batch_file_path = os.path.join(temp_dir, f"inst_fg_{package_name.replace('-', '_')}.bat")
                
                # Comando com CALL e redirecionamento para NUL
                batch_content = f'@echo off\nSET PYTHONIOENCODING=UTF-8\nCALL "{python_exe}" -m pip install --upgrade {package_name} > NUL 2> NUL'
                
                with open(batch_file_path, "w", encoding='utf-8') as f:
                    f.write(batch_content)
                
                process = subprocess.Popen(
                    [batch_file_path],
                    startupinfo=startupinfo,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                process.wait()
                
                try: os.remove(batch_file_path)
                except: pass

                if process.returncode != 0:
                    # Tenta com --user se falhar
                    QgsMessageLog.logMessage(f"Tentando {package_name} com --user...", "PortalForgegeo", Qgis.Info)
                    subprocess.call(f'"{python_exe}" -m pip install --upgrade --user {package_name}', 
                                    shell=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", package_name])

            # Após tentar instalar, atualiza o path e tenta importar
            update_python_path()
            try:
                importlib.import_module(import_name)
                QgsMessageLog.logMessage(f"Sucesso ao validar {package_name}", "PortalForgegeo", Qgis.Success)
            except:
                QgsMessageLog.logMessage(f"Falha ao validar {package_name} após instalação.", "PortalForgegeo", Qgis.Critical)
                success = False
                
        except Exception as e:
            QgsMessageLog.logMessage(f"Erro na instalação de {package_name}: {str(e)}", "PortalForgegeo", Qgis.Critical)
            success = False
    
    if success:
        QMessageBox.information(None, "Sucesso", "Instalada com sucesso!!! Seja benvindo ao GeoNexus.")
    else:
        QMessageBox.critical(None, "Erro", "Não foi possível validar algumas dependências. Tente reiniciar o QGIS.")
        
    return success
