# Guia de Instalação - Mosaic Clipper

## Pré-requisitos

Antes de instalar o Mosaic Clipper, certifique-se de ter:

1. **QGIS 3.40 ou superior** instalado
2. **Python 3.8 ou superior** (geralmente incluído com QGIS)
3. **Conta Google ativa** com acesso à API do Google Earth Engine
4. **Conexão com a Internet** para autenticação e processamento

## Passo 1: Preparar o Ambiente

### No Linux/Mac

Abra um terminal e instale a dependência do earthengine-api:

```bash
pip3 install earthengine-api
```

Ou, se estiver usando o Python do QGIS:

```bash
python3 -m pip install earthengine-api
```

### No Windows

Abra o Prompt de Comando (cmd.exe) ou PowerShell e execute:

```cmd
pip install earthengine-api
```

Se usar o Python do QGIS, pode executar via OSGeo4W Shell:

```cmd
python -m pip install earthengine-api
```

## Passo 2: Localizar o Diretório de Plugins do QGIS

### Linux/Mac

```bash
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

Ou, se estiver usando um perfil diferente:

```bash
~/.local/share/QGIS/QGIS3/profiles/[seu_perfil]/python/plugins/
```

### Windows

```
C:\Users\[Seu_Usuario]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
```

Ou, se estiver usando um perfil diferente:

```
C:\Users\[Seu_Usuario]\AppData\Roaming\QGIS\QGIS3\profiles\[seu_perfil]\python\plugins\
```

## Passo 3: Instalar o Plugin

### Opção A: Instalação Manual

1. Baixe o arquivo `mosaic_clipper_v*.zip`
2. Extraia o arquivo ZIP
3. Copie a pasta `mosaic_clipper` para o diretório de plugins do QGIS
4. Reinicie o QGIS

### Opção B: Instalação via Gerenciador de Plugins do QGIS

1. Abra o QGIS
2. Vá para **Plugins > Gerenciar e Instalar Plugins**
3. Procure por "Mosaic Clipper"
4. Clique em **Instalar**
5. Reinicie o QGIS

## Passo 4: Verificar a Instalação

1. Abra o QGIS
2. Vá para **Plugins > Gerenciar e Instalar Plugins**
3. Procure por "Mosaic Clipper"
4. Verifique se o plugin está marcado como "Instalado"
5. Feche o gerenciador de plugins

## Passo 5: Configurar Google Earth Engine

### Primeira Autenticação

1. Abra o plugin: **Plugins > Mosaic Clipper**
2. Clique em **"Autenticar com GEE"**
3. Uma janela do navegador será aberta automaticamente
4. Faça login com sua conta Google
5. Autorize o acesso à API do Google Earth Engine
6. Copie o código de autorização fornecido
7. Cole o código no console do QGIS (se solicitado)
8. Aguarde a confirmação de autenticação bem-sucedida

### Autenticações Subsequentes

Após a primeira autenticação, o plugin usará as credenciais armazenadas localmente. Você não precisará autenticar novamente a menos que as credenciais expirem ou sejam removidas.

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'ee'"

**Solução**: Instale o earthengine-api usando pip:

```bash
pip3 install earthengine-api
```

### Erro: "Falha ao autenticar com GEE"

**Possíveis causas e soluções**:

1. **Conta Google não tem acesso à API do Google Earth Engine**
   - Visite https://signup.earthengine.google.com/ e registre-se
   - Aguarde a aprovação (geralmente leva alguns dias)

2. **Credenciais expiradas**
   - Delete o arquivo de credenciais: `~/.config/earthengine/credentials`
   - Autentique novamente clicando em "Autenticar com GEE"

3. **Problema de conexão com a Internet**
   - Verifique sua conexão com a Internet
   - Tente autenticar novamente

### Erro: "Nenhuma imagem encontrada para [ano]"

**Possíveis causas e soluções**:

1. **Geometria fora da cobertura Landsat**
   - Verifique se a área de interesse está coberta pelo Landsat
   - Tente expandir o intervalo de anos

2. **Geometria em sistema de coordenadas incorreto**
   - Reprojete a camada para EPSG:4326 (WGS 84)
   - Use **Vector > Reproject Layer**

3. **Cobertura de nuvens muito alta**
   - Tente expandir o intervalo de anos para encontrar imagens com menos nuvens

### Erro: "A feição selecionada não possui geometria válida"

**Solução**:

1. Verifique se a camada vetorial contém feições
2. Repare a geometria usando **Vector > Geometry Tools > Check Validity**
3. Se necessário, recrie a camada vetorial

## Desinstalação

### Para Remover o Plugin

1. Abra o QGIS
2. Vá para **Plugins > Gerenciar e Instalar Plugins**
3. Procure por "Mosaic Clipper"
4. Clique em **Desinstalar**
5. Reinicie o QGIS

### Para Remover Credenciais do GEE

```bash
rm -rf ~/.config/earthengine/
```

## Suporte

Se encontrar problemas durante a instalação, visite:

- **Documentação do QGIS**: https://docs.qgis.org/
- **Google Earth Engine**: https://developers.google.com/earth-engine
- **Issues do Projeto**: https://github.com/geoservico/mosaic-clipper/issues
