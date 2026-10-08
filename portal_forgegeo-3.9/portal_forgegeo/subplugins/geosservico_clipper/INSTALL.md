# Guia de Instalação - GeoServiço-CLIPPER

## Pré-requisitos

### Sistema Operacional
- **Windows** 10/11 ou superior
- **Linux** (Ubuntu 20.04+, Debian, Fedora, etc.)
- **macOS** 10.15 ou superior

### Software Necessário
- **QGIS** 3.40 ou superior
- **Python** 3.8 ou superior (geralmente incluído com QGIS)
- **Git** (opcional, para clonar o repositório)
- **Conexão com Internet** (obrigatória)

### Conta Google
- Conta Google ativa
- Acesso aprovado ao Google Earth Engine (registre-se em https://earthengine.google.com)

## Passo 1: Registrar-se no Google Earth Engine

1. Visite https://earthengine.google.com
2. Clique em "Sign Up"
3. Faça login com sua conta Google
4. Preencha o formulário de registro
5. Aguarde a aprovação (geralmente 24-48 horas)

## Passo 2: Localizar Diretório de Plugins do QGIS

### Windows
```
C:\Users\[SEU_USUARIO]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
```

### Linux
```
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

### macOS
```
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

## Passo 3: Instalar o Plugin

### Opção A: Instalação Manual (Recomendado)

1. **Baixar o plugin**
   ```bash
   cd /caminho/para/plugins
   git clone https://github.com/geosservico/geosservico-clipper.git
   ```

   Ou baixar como ZIP e extrair:
   - Visite https://github.com/geosservico/geosservico-clipper
   - Clique em "Code" → "Download ZIP"
   - Extraia para o diretório de plugins com o nome `geosservico_clipper`

2. **Verificar estrutura**
   ```
   geosservico_clipper/
   ├── metadata.txt
   ├── __init__.py
   ├── geosservico_clipper.py
   ├── dialog.py
   ├── earth_engine_handler.py
   ├── utils.py
   ├── processing_provider.py
   ├── test_plugin.py
   ├── requirements.txt
   ├── README.md
   ├── INSTALL.md
   └── icon.png
   ```

3. **Reiniciar QGIS**

### Opção B: Instalação via Plugin Manager (Quando disponível)

1. Abra QGIS
2. Vá para **Plugins** → **Manage and Install Plugins**
3. Procure por "GeoServiço-CLIPPER"
4. Clique em **Install Plugin**

## Passo 4: Instalar Dependências Python

### Opção A: Via Console Python do QGIS (Recomendado)

1. Abra QGIS
2. Vá para **Plugins** → **Python Console**
3. Cole o seguinte código:

```python
import subprocess
import sys

# Instalar earthengine-api
print("Instalando earthengine-api...")
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'earthengine-api'])

# Instalar numpy (se não estiver)
print("Instalando numpy...")
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])

print("Dependências instaladas com sucesso!")
```

4. Pressione Enter para executar

### Opção B: Via Terminal/Prompt de Comando

**Windows (Command Prompt ou PowerShell):**
```bash
pip install earthengine-api numpy
```

**Linux/macOS (Terminal):**
```bash
pip3 install earthengine-api numpy
```

### Opção C: Usando requirements.txt

```bash
cd /caminho/para/geosservico_clipper
pip install -r requirements.txt
```

## Passo 5: Autenticar no Google Earth Engine

### Primeira Autenticação (Dentro do QGIS)

1. Abra QGIS
2. Vá para **Plugins** → **GeoServiço-CLIPPER** → **GeoServiço-CLIPPER - Recortar MapBiomas**
3. Na aba "Informações", clique em **"Autenticar no Earth Engine"**
4. Uma janela do navegador abrirá automaticamente
5. Faça login com sua conta Google
6. Autorize o acesso ao Earth Engine
7. Copie o código de autorização fornecido
8. Cole o código na janela de autenticação do QGIS
9. Clique em "OK"

### Autenticação via Terminal (Alternativa)

```bash
# Instalar earthengine-api se ainda não estiver
pip install earthengine-api

# Autenticar
earthengine authenticate
```

Isso abrirá uma janela do navegador para você autorizar o acesso.

## Passo 6: Verificar Instalação

1. Abra QGIS
2. Vá para **Plugins** → **Manage and Install Plugins**
3. Procure por "GeoServiço-CLIPPER"
4. Verifique se está marcado como "Installed"
5. Se não estiver habilitado, clique no checkbox para habilitar

## Passo 7: Testar o Plugin

1. Abra um projeto QGIS
2. Importe uma camada vetorial (shapefile, GeoJSON, etc.)
3. Vá para **Plugins** → **GeoServiço-CLIPPER** → **GeoServiço-CLIPPER - Recortar MapBiomas**
4. Selecione a camada vetorial
5. Escolha um ano (ex: 2024)
6. Clique em "Recortar MapBiomas"
7. Acompanhe o progresso na barra de progresso

## Troubleshooting

### Problema: Plugin não aparece no menu

**Solução:**
1. Verifique se está no diretório correto de plugins
2. Verifique se o arquivo `metadata.txt` está presente
3. Reinicie o QGIS
4. Vá para **Plugins** → **Manage and Install Plugins** e procure por "GeoServiço-CLIPPER"

### Problema: "earthengine-api não está instalado"

**Solução:**
```python
# No console Python do QGIS:
import subprocess
import sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'earthengine-api'])
```

### Problema: "Não autenticado no Earth Engine"

**Solução:**
1. Verifique se tem acesso aprovado ao Earth Engine
2. Clique em "Autenticar no Earth Engine" no plugin
3. Faça login com a mesma conta Google usada para registrar no Earth Engine
4. Autorize o acesso

### Problema: "Permissão negada" ao instalar

**Windows:**
- Execute o Command Prompt como administrador
- Tente instalar novamente

**Linux/macOS:**
```bash
pip install --user earthengine-api
```

### Problema: Plugin não funciona após atualização do QGIS

**Solução:**
1. Desabilite o plugin em **Plugins** → **Manage and Install Plugins**
2. Feche o QGIS
3. Reinstale as dependências:
   ```bash
   pip install --upgrade earthengine-api
   ```
4. Abra o QGIS novamente
5. Habilite o plugin

## Desinstalação

### Remover Plugin

1. Feche o QGIS
2. Delete a pasta `geosservico_clipper` do diretório de plugins
3. Abra o QGIS novamente

### Remover Dependências (Opcional)

```bash
pip uninstall earthengine-api
```

## Suporte

Se encontrar problemas durante a instalação:

1. Consulte a documentação: https://github.com/geosservico/geosservico-clipper
2. Abra uma issue no GitHub: https://github.com/geosservico/geosservico-clipper/issues
3. Entre em contato: contato@geoservico.com.br

## Próximos Passos

Após a instalação bem-sucedida:

1. Leia o [README.md](README.md) para entender as funcionalidades
2. Consulte o [Guia de Uso](README.md#uso) para aprender a usar o plugin
3. Explore os exemplos de dados MapBiomas em https://brasil.mapbiomas.org

---

**Desenvolvido com ❤️ para a comunidade geoespacial brasileira**
