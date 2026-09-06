# Mosaic Clipper - Plugin QGIS

## Descrição

**Mosaic Clipper** é um plugin QGIS profissional para download e carregamento automático de imagens Landsat (2000-2025) em falsa cor via Google Earth Engine. O plugin integra-se perfeitamente com o QGIS 3.40+ e oferece uma interface intuitiva para processar séries temporais de imagens de satélite, carregando-as automaticamente como camadas raster.

### Características Principais

- **Autenticação Obrigatória**: Requer login com credenciais do Google Earth Engine e ID do Projeto Google Cloud
- **Série Temporal Landsat**: Suporta dados de 2000 a 2025
- **Falsa Cor Automática**: Composição SWIR1-NIR-Red para análise de vegetação
- **Recorte por Máscara**: Utiliza camadas vetoriais do QGIS como máscara de recorte
- **Download Local Automático**: Imagens são baixadas e carregadas automaticamente no QGIS
- **Seleção de Satélite Automática**: Escolhe a coleção Landsat apropriada por ano
  - Landsat 5 (TM): 2000-2011
  - Landsat 7 (ETM+): 2012-2013
  - Landsat 8/9 (OLI): 2014-2025
- **Melhor Imagem**: Seleciona automaticamente a imagem com menor cobertura de nuvens
- **Interface Intuitiva**: Dialog com seletores de camada, intervalo de anos e botão de processamento

## Requisitos

- **QGIS**: 3.40 ou superior
- **Python**: 3.8 ou superior
- **Google Earth Engine**: Conta ativa com acesso à API
- **Google Cloud Project**: Projeto ativo com API do Earth Engine habilitada
- **Dependência**: earthengine-api (instalada automaticamente)

## Instalação

1. Baixe o arquivo `mosaic_clipper_v*.zip`
2. Extraia a pasta `mosaic_clipper` para o diretório de plugins do QGIS:
   - **Linux/Mac**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows**: `C:\Users\[Usuario]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
3. Reinicie o QGIS
4. Ative o plugin em **Plugins > Gerenciar e Instalar Plugins** (procure por "Mosaic Clipper")

## Uso

### Passo 1: Autenticação

1. Abra o plugin: **Plugins > Mosaic Clipper**
2. Insira seu **ID do Projeto Google Cloud** no campo de texto (ex: `meu-projeto-12345`)
3. Clique em **"Autenticar com GEE"**
4. Siga as instruções no console para fazer login com sua conta Google
5. Após autenticação bem-sucedida, o status mudará para "✓ Autenticado com sucesso!"

**Nota**: Você precisa ter um projeto Google Cloud ativo com a API do Google Earth Engine habilitada. Visite https://console.cloud.google.com/ para criar um projeto se necessário.

### Passo 2: Preparar Dados

1. Carregue uma camada vetorial no QGIS (Shapefile, GeoPackage, etc.) que será usada como máscara
2. Certifique-se de que a geometria está em coordenadas geográficas (EPSG:4326)

### Passo 3: Configurar Parâmetros

1. **Selecionar Camada Vetorial**: Escolha a camada que será usada como máscara
2. **Ano Inicial e Final**: Selecione o intervalo de anos desejado (2000-2025)

### Passo 4: Processar

1. Clique em **"Baixar e Carregar Imagens"**
2. O plugin processará cada ano da série temporal
3. As imagens recortadas serão:
   - **Baixadas localmente** no diretório temporário do sistema
   - **Carregadas automaticamente** como camadas raster no QGIS
4. Você receberá uma mensagem de confirmação com o número de imagens processadas

**Importante**: As imagens aparecerão na lista de camadas do QGIS e poderão ser manipuladas imediatamente.

## Saída

O plugin gera arquivos GeoTIFF com a seguinte nomenclatura:

```
[NomeCamada]_[Ano]_[IDImagem].tif
```

Exemplo: `Fazenda_Vale_da_Paz_2020_LC08_L2SP_220063_20200715_20200815_02_T1.tif`

### Local de Armazenamento

- **Localmente**: Os arquivos são salvos no diretório temporário do sistema (`/tmp` no Linux/Mac ou `C:\Users\[Usuario]\AppData\Local\Temp` no Windows) e carregados automaticamente no QGIS

### Composição de Falsa Cor

A imagem é exportada em composição RGB com:
- **R (Vermelho)**: Banda Red (SR_B3 ou SR_B4)
- **G (Verde)**: Banda NIR (SR_B4 ou SR_B5)
- **B (Azul)**: Banda SWIR1 (SR_B5 ou SR_B6)

Esta composição realça a vegetação em tons de vermelho/rosa, facilitando análises de cobertura vegetal.

## Estrutura do Projeto

```
mosaic_clipper/
├── __init__.py              # Ponto de entrada do plugin
├── plugin.py                # Classe principal do plugin
├── dialog.py                # Interface gráfica (QDialog)
├── gee_handler.py           # Integração com Google Earth Engine
├── utils.py                 # Funções auxiliares
├── metadata.txt             # Metadados do plugin
├── requirements.txt         # Dependências Python
├── icon.png                 # Ícone do plugin
├── README.md                # Este arquivo
└── INSTALL.md               # Instruções de instalação
```

## Troubleshooting

### Erro: "Nenhuma imagem encontrada para [ano]"
- Verifique se a geometria está dentro da cobertura Landsat
- Tente expandir o intervalo de anos
- Certifique-se de que a geometria está em coordenadas geográficas (EPSG:4326)

### Erro: "A feição selecionada não possui geometria válida"
- Verifique se a camada vetorial contém feições válidas
- Repare a geometria usando **Vector > Geometry Tools > Check Validity**

### Erro de Autenticação GEE
- Certifique-se de ter uma conta Google ativa
- Verifique se tem acesso à API do Google Earth Engine
- Tente autenticar novamente clicando em "Autenticar com GEE"

### As imagens não aparecem no QGIS após o download
- Verifique se a pasta de camadas está visível no painel esquerdo
- Verifique o console do QGIS para mensagens de erro
- Tente recarregar o projeto

## Licença

Este plugin é desenvolvido por Tecno. Geoproc. Fabrício Marçal.

## Suporte

Para reportar bugs ou sugerir melhorias, visite: https://github.com/geoservico/mosaic-clipper/issues

## Suporte a Geometrias

O plugin suporta os seguintes tipos de geometria vetorial:

- **Polygon**: Poligonos simples (uma unica geometria por feicao)
- **MultiPolygon**: Multiplos poligonos em uma unica feicao
  - Para MultiPolygon, o plugin usa o bounding box (retangulo envolvente) para criar uma geometria valida para o Google Earth Engine
  - Isso garante que toda a area seja coberta, mesmo com geometrias complexas

## Changelog

### v0.0.5 (2026-02-23)
- Correcao definitiva: Extracao robusta de coordenadas para MultiPolygon
- Multiplas estrategias de conversao para maxima compatibilidade
- Suporte garantido para qualquer tipo de geometria poligonal

### v0.0.4 (2026-02-23)
- Correcao: Suporte para geometrias MultiPolygon
- Melhoria: Usa bounding box para converter MultiPolygon em Polygon valido para EE
- Robustez: Melhor tratamento de diferentes tipos de geometria vetorial

### v0.0.3 (2026-02-23)
- Simplificação: Remoção da exportação para Google Drive
- Foco exclusivo: Download local e carregamento automático de raster no QGIS
- Melhoria: Interface simplificada sem campo de pasta de destino
- Otimização: Fluxo de processamento mais rápido e direto

### v0.0.2 (2026-02-23)
- Correção: Campo Project ID obrigatório para inicialização do GEE
- Nova funcionalidade: Carregamento automático de raster no QGIS após download
- Melhoria: Download local de imagens além de exportação para Google Drive
- Atualização: Interface gráfica com campo de entrada para Project ID

### v0.0.1 (2026-02-23)
- Versão inicial do plugin Mosaic Clipper
- Integração com Google Earth Engine
- Suporte para série temporal Landsat (2000-2025)
- Interface gráfica com autenticação obrigatória
- Recorte e exportação de imagens em falsa cor
