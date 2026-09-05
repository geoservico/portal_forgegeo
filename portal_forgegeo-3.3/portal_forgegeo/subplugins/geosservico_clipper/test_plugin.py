# -*- coding: utf-8 -*-
"""
Testes para o plugin GeoServiço-CLIPPER
"""

import unittest
import sys
import os
from pathlib import Path

# Adicionar diretório do plugin ao path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)


class TestEarthEngineHandler(unittest.TestCase):
    """Testes para o módulo EarthEngineHandler"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        try:
            from earth_engine_handler import EarthEngineHandler
            self.handler = EarthEngineHandler()
        except ImportError:
            self.skipTest("earthengine-api não está instalado")
    
    def test_available_years(self):
        """Testar lista de anos disponíveis"""
        years = self.handler.get_available_years()
        self.assertEqual(len(years), 40)  # 1985-2024
        self.assertEqual(years[0], 1985)
        self.assertEqual(years[-1], 2024)
    
    def test_classification_legend(self):
        """Testar legenda de classificação"""
        legend = self.handler.get_classification_legend()
        self.assertIsInstance(legend, dict)
        self.assertIn(3, legend)  # Formação Florestal
        self.assertIn(15, legend)  # Pastagem
        self.assertIn(18, legend)  # Agricultura


class TestUtils(unittest.TestCase):
    """Testes para o módulo utils"""
    
    def test_get_plugin_path(self):
        """Testar obtenção do caminho do plugin"""
        from utils import get_plugin_path
        path = get_plugin_path()
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isdir(path))
    
    def test_is_valid_year(self):
        """Testar validação de ano"""
        from utils import is_valid_year
        self.assertTrue(is_valid_year(2024))
        self.assertTrue(is_valid_year(1985))
        self.assertTrue(is_valid_year(2000))
        self.assertFalse(is_valid_year(1984))
        self.assertFalse(is_valid_year(2025))
    
    def test_format_file_size(self):
        """Testar formatação de tamanho de arquivo"""
        from utils import format_file_size
        self.assertEqual(format_file_size(512), "512.00 B")
        self.assertEqual(format_file_size(1024), "1.00 KB")
        self.assertEqual(format_file_size(1048576), "1.00 MB")
    
    def test_get_mapbiomas_legend(self):
        """Testar obtenção da legenda MapBiomas"""
        from utils import get_mapbiomas_legend
        legend = get_mapbiomas_legend()
        self.assertIsInstance(legend, dict)
        self.assertGreater(len(legend), 30)


class TestMetadata(unittest.TestCase):
    """Testes para arquivo metadata.txt"""
    
    def test_metadata_exists(self):
        """Testar se metadata.txt existe"""
        metadata_path = os.path.join(plugin_dir, 'metadata.txt')
        self.assertTrue(os.path.exists(metadata_path))
    
    def test_metadata_content(self):
        """Testar conteúdo do metadata.txt"""
        metadata_path = os.path.join(plugin_dir, 'metadata.txt')
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar campos obrigatórios
        self.assertIn('name=GeoServiço-CLIPPER', content)
        self.assertIn('qgisMinimumVersion=3.40', content)
        self.assertIn('version=1.0.0', content)
        self.assertIn('author=Tecno. Geoproc. Fabrício Marçal', content)


class TestPluginStructure(unittest.TestCase):
    """Testes para estrutura do plugin"""
    
    def test_required_files_exist(self):
        """Testar se arquivos obrigatórios existem"""
        required_files = [
            'metadata.txt',
            '__init__.py',
            'geosservico_clipper.py',
            'dialog.py',
            'earth_engine_handler.py',
            'utils.py'
        ]
        
        for filename in required_files:
            filepath = os.path.join(plugin_dir, filename)
            self.assertTrue(
                os.path.exists(filepath),
                f"Arquivo obrigatório não encontrado: {filename}"
            )
    
    def test_init_py_has_class_factory(self):
        """Testar se __init__.py tem função classFactory"""
        init_path = os.path.join(plugin_dir, '__init__.py')
        
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('def classFactory', content)


def run_tests():
    """Executar todos os testes"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEarthEngineHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestPluginStructure))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
