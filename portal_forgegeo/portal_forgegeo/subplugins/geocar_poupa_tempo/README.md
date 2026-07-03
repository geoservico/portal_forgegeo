# CAR/Pa - Poupa tempo

Plugin para QGIS 3.40+ que automatiza a criação de grupos e camadas para o Cadastro Ambiental Rural (CAR).

## Desenvolvido por
**Geoserviço - Geotecnologias & Meio Ambiente**  
**Autor:** GEOSERVIÇO

## Funcionalidades

### Criação Automática de Grupos e Camadas
O plugin cria automaticamente a estrutura completa de grupos e camadas necessárias para o CAR:

#### 1. Grupo Imóvel
- Imóvel (multipolígono)
- Sede (ponto)

#### 2. Grupo Cobertura do Solo
- Área Consolidada (multipolígono)
- Remanescente de Vegetação Nativa (multipolígono)
- Área de Pousio (multipolígono)
- Área de Regeneração (multipolígono)

#### 3. Grupo Servidão Administrativa
- Infraestrutura Pública (multipolígono e linha)
- Utilidade Pública (multipolígono e linha)
- Reservatório para Abastecimento ou Geração de Energia (multipolígono)
- Servidão Minerária (multipolígono)

#### 4. Grupo APP/Uso Restrito
##### Subgrupo: Uso Restrito
- Área de Uso Restrito para declividade de 25 a 45 graus (multipolígono)
- Área de Uso Restrito para regiões pantaneiras (multipolígono)

##### Subgrupo: Área de Preservação Permanente
- Curso d'água natural com até 10 metros (multipolígono e linha)
- Curso d'água natural de 10 a 50 metros (multipolígono)
- Curso d'água natural de 50 a 200 metros (multipolígono)
- Curso d'água natural de 200 a 600 metros (multipolígono)
- Curso d'água natural acima de 600 metros (multipolígono)
- Lago ou lagoa natural (multipolígono)
- Nascente ou olho d'água perene (ponto)
- Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais (multipolígono)
- Reservatório de geração de energia elétrica construído até 24/08/2001 (multipolígono)
- Banhado (multipolígono)
- Manguezal (multipolígono)
- Restinga (multipolígono)
- Vereda (multipolígono)
- Área com altitude superior a 1.800 metros (multipolígono)
- Área de declividade maior que 45 graus (multipolígono)
- Borda de chapada (multipolígono)
- Área de topo de morro (multipolígono)

#### 5. Grupo Reserva Legal
- Reserva Legal Proposta (multipolígono)
- Reserva Legal Averbada (multipolígono)
- Reserva Legal Aprovada e não Averbada (multipolígono)
- Reserva legal vinculada à compensação de outro imóvel (multipolígono)

### Exportação Automática
- Exporta todas as camadas em formato ZIP
- Sistema de coordenadas: SIRGAS 2000 (EPSG:4674) - Coordenadas Geográficas
- Cria automaticamente a pasta "CAR FINALIZADO" no desktop
- Cada camada é exportada como um shapefile compactado

### Interface Moderna
- Interface intuitiva e moderna
- Seleção individual de grupos de camadas
- Barra de progresso para acompanhar operações
- Log detalhado das operações
- Opção de exportação automática após criação

## Instalação

1. Baixe o plugin completo
2. Copie a pasta `CAR_Pa_Poupa_Tempo` para o diretório de plugins do QGIS:
   - Windows: `C:\Users\[usuário]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - Mac: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Reinicie o QGIS
4. Ative o plugin em Plugins > Gerenciar e Instalar Plugins

## Como Usar

1. Clique no ícone do plugin na barra de ferramentas ou acesse via menu Plugins
2. Selecione os grupos de camadas que deseja criar
3. Clique em "Criar Camadas"
4. Opcionalmente, clique em "Exportar Camadas" para gerar os arquivos ZIP

## Requisitos

- QGIS 3.40 ou superior
- Sistema operacional: Windows, Linux ou macOS

## Suporte

Para suporte técnico, entre em contato com:
**Geoserviço - Geotecnologias & Meio Ambiente**

## Licença

Este plugin foi desenvolvido especificamente para uso profissional em projetos de CAR.

## Versão

Versão 1.0 - Primeira versão estável

