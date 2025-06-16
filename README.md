# `main.py`: Confluent Cloud Resource and Role Binding Auditor

Este script Python (`main.py`) é uma ferramenta para **auditar e coletar informações** sobre seus recursos e permissões no **Confluent Cloud**. Ele interage com as APIs do Confluent Cloud para:

* **Descobrir IDs** de organizações, ambientes, clusters Kafka e Schema Registry.
* **Listar tópicos Kafka** e **subjects do Schema Registry** em seus clusters.
* **Identificar e agregar todos os `Role Bindings`** (associações de função) para suas `Service Accounts` em diversos níveis de recursos, incluindo:
    * Organização
    * Ambiente
    * Cluster Kafka
    * Tópico Kafka
    * Cluster Schema Registry
    * Subject do Schema Registry

## Como Funciona

O script utiliza:

* **`python-dotenv`**: Para carregar suas **credenciais de API de forma segura** a partir de um arquivo `.env` (ex: `variables.env`), garantindo que suas chaves não fiquem expostas diretamente no código.
* **Mapeamento de Credenciais por Ambiente**: As credenciais para APIs de dados (Kafka e Schema Registry) são gerenciadas por ambiente, permitindo que você use diferentes pares de chaves para diferentes ambientes (ex: desenvolvimento, produção).
* **Função Genérica de Requisição**: Uma função auxiliar (`make_api_request`) lida com todas as chamadas à API da Confluent Cloud, incluindo autenticação dinâmica (escolhendo as credenciais corretas com base no tipo de endpoint e ambiente) e lógica de retries para lidar com limites de taxa.
* **Descoberta Abrangente**: Assegura que todas as `Service Accounts` e os recursos associados (tópicos, subjects, etc.) sejam escaneados para fornecer uma visão completa das permissões.

## Estrutura do Projeto

* **`main.py`**: O script principal que contém toda a lógica para interagir com as APIs do Confluent Cloud e coletar os dados.
* **`variables.env`**: Um arquivo oculto (não deve ser versionado no Git) que armazena suas chaves de API da Confluent Cloud e credenciais específicas por ambiente.
* **`test_confluent_api.py`**: Um script de teste unitário simples para validar a lógica de autenticação da função `make_api_request`, simulando chamadas de API sem interações reais de rede.

## Uso

Para usar o script, você precisará:

1.  **Configurar suas credenciais** no arquivo `variables.env` (veja o exemplo em `test_confluent_api.py` para os nomes das variáveis).
2.  **Executar o `main.py`** para iniciar o processo de auditoria e obter um resumo dos `Role Bindings` encontrados.

Este projeto visa fornecer uma **ferramenta clara e eficiente** para entender e monitorar as permissões em seu ambiente Confluent Cloud.