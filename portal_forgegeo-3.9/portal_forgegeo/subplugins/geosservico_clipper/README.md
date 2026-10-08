# GeoServiço-CLIPPER

Plugin QGIS 3.40+ para recortar imagens MapBiomas via Google Earth Engine usando máscara vetorial.

## Descrição

**GeoServiço-CLIPPER** é um plugin para QGIS que permite recortar imagens de uso e cobertura do solo do projeto MapBiomas utilizando uma camada vetorial como máscara. O plugin integra-se com o Google Earth Engine para acessar os dados do MapBiomas Collection 10 e exportar imagens recortadas diretamente como camadas no projeto QGIS.

## Características

- ✅ Integração com Google Earth Engine
- ✅ Acesso a dados MapBiomas Collection 10 (1985-2024)
- ✅ Recorte de imagens usando geometrias vetoriais
- ✅ Exportação automática de resultados como camadas QGIS
- ✅ Interface gráfica intuitiva
- ✅ Suporte a múltiplas geometrias
- ✅ Reprojeção automática de dados
- ✅ Log detalhado de operações
- ✅ Validação de credenciais Earth Engine

## Requisitos

### Sistema
- **QGIS**: Versão 3.40 ou superior
- **Python**: 3.8 ou superior
- **Conexão**: Internet (obrigatória para Google Earth Engine)

### Dependências Python
- `qgis` (PyQGIS)
- `earthengine-api` (para integração com Earth Engine)
- `numpy` (processamento de dados)
- `gdal` (manipulação de rasters)

### Conta Google
- Conta Google ativa
- Acesso ao Google Earth Engine (registre-se em https://earthengine.google.com)

## Instalação

### 1. Baixar o Plugin

Clone ou baixe o repositório:

```bash
git clone https://github.com/geosservico/geosservico-clipper.git
```

### 2. Instalar no QGIS

**Opção A: Instalação Manual**

1. Localize o diretório de plugins do QGIS:
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Copie a pasta `geosservico_clipper` para o diretório de plugins

3. Reinicie o QGIS

**Opção B: Instalação via Plugin Manager (em breve)**

O plugin será disponibilizado no repositório oficial de plugins QGIS.

### 3. Instalar Dependências

Abra o console Python do QGIS e execute:

```python
import subprocess
import sys

# Instalar earthengine-api
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'earthengine-api'])
```

Ou via terminal:

```bash
pip install earthengine-api
```

## Uso

### 1. Preparar Dados

- Abra um projeto QGIS
- Importe uma camada vetorial que será usada como máscara (polígono, multiponto, etc.)

### 2. Abrir o Plugin

No menu QGIS, vá para:
```
Plugins → GeoServiço-CLIPPER → GeoServiço-CLIPPER - Recortar MapBiomas
```

Ou clique no ícone da barra de ferramentas.

### 3. Configurar Parâmetros

1. **Camada Vetorial**: Selecione a camada que será usada como máscara
2. **Ano**: Escolha o ano desejado (1985-2024)
3. **Coleção**: Selecione a coleção MapBiomas (recomendado: Collection 10)
4. **Arquivo de Saída** (opcional): Especifique um caminho para salvar o arquivo

### 4. Autenticar no Earth Engine

1. Clique em "Autenticar no Earth Engine"
2. Uma janela do navegador abrirá
3. Faça login com sua conta Google
4. Autorize o acesso ao Earth Engine
5. Copie o código de autorização
6. Cole o código na janela de autenticação do QGIS

### 5. Processar Recorte

1. Clique em "Recortar MapBiomas"
2. Acompanhe o progresso na barra de progresso
3. Consulte o log para detalhes da operação
4. A imagem recortada será adicionada automaticamente ao projeto

## Estrutura do Plugin

```
geosservico_clipper/
├── metadata.txt                 # Metadados do plugin
├── __init__.py                 # Ponto de entrada
├── geosservico_clipper.py      # Classe principal
├── dialog.py                   # Interface gráfica
├── earth_engine_handler.py     # Integração com Earth Engine
├── utils.py                    # Funções utilitárias
├── icon.png                    # Ícone do plugin
└── README.md                   # Este arquivo
```

## Dados MapBiomas

### Informações Técnicas

| Propriedade | Valor |
|---|---|
| **Fonte** | MapBiomas Collection 10 |
| **Resolução** | 30 metros |
| **CRS** | EPSG:4326 (WGS84) |
| **Período** | 1985-2024 |
| **Satélite** | Landsat 5, 7, 8, 9 |
| **Banda** | classification (valores categóricos) |

### Classes de Uso/Cobertura do Solo

O MapBiomas classifica os pixels em diferentes categorias:

- **Florestas**: Formação Florestal, Savânica, Manguezal, Plantação Florestal, etc.
- **Agricultura**: Soja, Arroz, Cana-de-Açúcar, Café, Citrus, Algodão, etc.
- **Pastagem**: Pastagem, Pastagem Natural
- **Água**: Rios, Lagos, Oceano, Aquicultura
- **Áreas Urbanas**: Área Urbana
- **Outras**: Mineração, Áreas Úmidas, Recifes de Coral, etc.

Consulte a legenda completa na aba "Informações" do plugin.

## Troubleshooting

### Erro: "Não autenticado no Earth Engine"

**Solução:**
1. Clique em "Autenticar no Earth Engine"
2. Certifique-se de ter uma conta Google ativa
3. Registre-se no Earth Engine: https://earthengine.google.com
4. Aguarde a aprovação (pode levar algumas horas)

### Erro: "earthengine-api não está instalado"

**Solução:**
```bash
pip install earthengine-api
```

Ou via console Python do QGIS:
```python
import subprocess
import sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'earthengine-api'])
```

### Erro: "Nenhuma imagem encontrada para o ano"

**Solução:**
- Verifique se o ano está dentro do intervalo 1985-2024
- Certifique-se de que a coleção selecionada contém dados para esse ano
- Consulte a documentação do MapBiomas

### Erro: "Falha ao processar recorte"

**Solução:**
1. Verifique a conexão com a internet
2. Valide a camada vetorial (deve conter geometrias válidas)
3. Consulte o log para detalhes do erro
4. Tente com uma geometria menor

## Documentação

Para mais informações sobre MapBiomas, visite:
- Website: https://mapbiomas.org
- Documentação: https://brasil.mapbiomas.org
- Earth Engine: https://developers.google.com/earth-engine

## Suporte

Para reportar bugs ou solicitar funcionalidades:
- GitHub Issues: https://github.com/geosservico/geosservico-clipper/issues
- Email: contato@geoservico.com.br

## Licença

Este plugin está licenciado sob a licença GPL v3.

## Autor

**Tecno. Geoproc. Fabrício Marçal**
- Email: contato@geoservico.com.br
- Website: https://geoservico.com.br

## Changelog

### v1.0.0 (2026-02-17)
- Versão inicial do plugin
- Suporte a MapBiomas Collection 10
- Integração com Google Earth Engine
- Interface gráfica completa
- Recorte de imagens com máscara vetorial
- Exportação automática como camadas QGIS

## Agradecimentos

- MapBiomas pelo acesso aos dados
- Google Earth Engine pela plataforma
- Comunidade QGIS pelo suporte

---

**Desenvolvido com ❤️ para a comunidade geoespacial brasileira**
