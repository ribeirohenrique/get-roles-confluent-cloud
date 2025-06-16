from pathlib import Path
from dotenv import load_dotenv
import os  # Importar o módulo os para usar os.getenv
import requests
import json
import time

dotenv_path = Path('./variables.env')
load_dotenv(dotenv_path=dotenv_path)
CONFLUENT_CLOUD_API_KEY = os.getenv('CONFLUENT_CLOUD_API_KEY')
CONFLUENT_CLOUD_API_SECRET = os.getenv('CONFLUENT_CLOUD_API_SECRET')
ENVIRONMENT_CREDENTIALS = {
    "env-qzn062": {
        "api_key": os.getenv('ENV_QZN062_API_KEY'),
        "api_secret": os.getenv('ENV_QZN062_API_SECRET'),
        "sr_api_key": os.getenv('ENV_QZN062_SR_API_KEY'),
        "sr_api_secret": os.getenv('ENV_QZN062_SR_API_SECRET')
    },
    "env-qz3jzd": {
        "api_key": os.getenv('ENV_QZ3JZD_API_KEY'),
        "api_secret": os.getenv('ENV_QZ3JZD_API_SECRET'),
        "sr_api_key": os.getenv('ENV_QZ3JZD_SR_API_KEY'),
        "sr_api_secret": os.getenv('ENV_QZ3JZD_SR_API_SECRET')
    },
    # Adicione outros ambientes conforme necessário, seguindo o padrão
    # "env-outro-id": {
    #     "api_key": os.getenv('ENV_OUTROID_API_KEY'),
    #     "api_secret": os.getenv('ENV_OUTROID_API_SECRET'),
    #     "sr_api_key": os.getenv('ENV_OUTROID_SR_API_KEY'),
    #     "sr_api_secret": os.getenv('ENV_OUTROID_SR_API_SECRET')
    # },
}
API_BASE_URL = "https://api.confluent.cloud"
CLUSTER_BASE_URL = "https://pkc-n3603.us-central1.gcp.confluent.cloud:443"  # Este pode vir do .env também, se variar.


# --- Métodos Auxiliares ---
def make_api_request(method, endpoint, params=None, data=None, attempt=1, max_attempts=3, environment_id=None):
    headers = {"Content-Type": "application/json"}
    auth = None
    if environment_id and environment_id in ENVIRONMENT_CREDENTIALS:
        creds = ENVIRONMENT_CREDENTIALS[environment_id]
        if "/subjects" in endpoint or "/schemas" in endpoint or "/mode" in endpoint:
            # Verifica se as chaves SR existem para o ambiente
            if creds.get('sr_api_key') and creds.get('sr_api_secret'):
                auth = (creds['sr_api_key'], creds['sr_api_secret'])
            else:
                auth = (CONFLUENT_CLOUD_API_KEY, CONFLUENT_CLOUD_API_SECRET)
        elif endpoint.startswith(CLUSTER_BASE_URL):
            if creds.get('api_key') and creds.get('api_secret'):
                auth = (creds['api_key'], creds['api_secret'])
            else:
                auth = (CONFLUENT_CLOUD_API_KEY, CONFLUENT_CLOUD_API_SECRET)
        else:
            auth = (CONFLUENT_CLOUD_API_KEY, CONFLUENT_CLOUD_API_SECRET)
    else:
        auth = (CONFLUENT_CLOUD_API_KEY, CONFLUENT_CLOUD_API_SECRET)
        if environment_id:
            print(
                f"  Aviso: Credenciais para o ambiente '{environment_id}' não configuradas ou ausentes no .env. Usando credenciais padrão.")
    if auth is None:
        print("  Erro: Nenhuma credencial de autenticação foi selecionada. Usando fallback para chaves gerais.")
        auth = (CONFLUENT_CLOUD_API_KEY, CONFLUENT_CLOUD_API_SECRET)

    if not all(auth):
        print("  Erro: Uma ou mais chaves de autenticação estão vazias. Verifique seu arquivo .env e o mapeamento.")
        return None

    try:
        response = requests.request(method, endpoint, headers=headers, auth=auth, params=params, json=data, timeout=30)
        if response.status_code == 429:
            if attempt < max_attempts:
                retry_after = int(response.headers.get("Retry-After", "10"))
                print(
                    f"Rate limit atingido. Tentando novamente em {retry_after} segundos... (Tentativa {attempt}/{max_attempts})")
                time.sleep(retry_after)
                return make_api_request(method, endpoint, params, data, attempt + 1, max_attempts, environment_id)
            else:
                print(f"Rate limit atingido. Máximo de tentativas ({max_attempts}) alcançado.")
                response.raise_for_status()

        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()
    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh} (Status: {errh.response.status_code})")
        try:
            print(f"Response content: {errh.response.json()}")
        except json.JSONDecodeError:
            print(f"Response content: {errh.response.text}")
    except requests.exceptions.RequestException as err:
        print(f"Request Exception: {err}")
    return None

def get_service_accounts():
    accounts = []
    service_account_endpoint = f"{API_BASE_URL}/iam/v2/service-accounts"
    service_account_response = make_api_request("GET", service_account_endpoint)
    if service_account_response and 'data' in service_account_response and isinstance(service_account_response['data'],
                                                                                      list):
        for item in service_account_response['data']:
            if 'id' in item:
                accounts.append(item['id'])
    else:
        print(f"Nenhum dado de service_accounts encontrado ou resposta da API inválida.")
    return accounts


def get_organizations():
    organizations = []
    organization_endpoint = f"{API_BASE_URL}/org/v2/organizations"
    organization_endpoint_response = make_api_request("GET", organization_endpoint)
    if organization_endpoint_response and 'data' in organization_endpoint_response and isinstance(
            organization_endpoint_response['data'], list):
        for item in organization_endpoint_response['data']:
            if 'id' in item:
                organizations.append(item['id'])
    else:
        print("Nenhum dado de organizations encontrado ou resposta da API inválida.")
    return organizations


def get_environments():
    environments = []
    environment_endpoint = f"{API_BASE_URL}/org/v2/environments"
    environment_endpoint_response = make_api_request("GET", environment_endpoint)
    if environment_endpoint_response and 'data' in environment_endpoint_response and isinstance(
            environment_endpoint_response['data'], list):
        for item in environment_endpoint_response['data']:
            if 'id' in item:
                environments.append(item['id'])
    else:
        print("Nenhum dado de environments encontrado ou resposta da API inválida.")
    return environments


def get_clusters(environments):
    clusters_info = []
    for environment_id in environments:
        cluster_endpoint = f"{API_BASE_URL}/cmk/v2/clusters?environment={environment_id}"
        cluster_endpoint_response = make_api_request("GET", cluster_endpoint)
        if cluster_endpoint_response and 'data' in cluster_endpoint_response and isinstance(
                cluster_endpoint_response['data'], list):
            for item in cluster_endpoint_response['data']:
                if 'id' in item:
                    clusters_info.append((item['id'], environment_id))
        else:
            print(f"Nenhum dado de clusters no environment {environment_id} encontrado ou resposta da API inválida.")
    return clusters_info


def get_topics(clusters_info):
    topics = []
    for cluster_id, environment_id in clusters_info:
        topic_endpoint = f"{CLUSTER_BASE_URL}/kafka/v3/clusters/{cluster_id}/topics"
        topic_endpoint_response = make_api_request("GET", topic_endpoint, environment_id=environment_id)

        if topic_endpoint_response and 'data' in topic_endpoint_response and isinstance(topic_endpoint_response['data'],
                                                                                        list):
            for item in topic_endpoint_response['data']:
                if 'topic_name' in item:
                    topics.append(item['topic_name'])
        else:
            print(f"Nenhum tópico encontrado no cluster {cluster_id} ou resposta da API inválida.")
    return topics


def get_schema_registry_clusters_endpoints(environments):
    sr_clusters_info = []
    for environment_id in environments:
        sr_cluster_list_endpoint = f"{API_BASE_URL}/srcm/v3/clusters?environment={environment_id}"
        sr_list_response = make_api_request("GET", sr_cluster_list_endpoint)

        if sr_list_response and 'data' in sr_list_response and isinstance(sr_list_response['data'], list):
            for item in sr_list_response['data']:
                if 'spec' in item and isinstance(item['spec'], dict):
                    if 'http_endpoint' in item['spec'] and 'id' in item:
                        sr_clusters_info.append((item['spec']['http_endpoint'], environment_id, item['id']))
                    else:
                        print(
                            f"Aviso: 'http_endpoint' ou 'id' não encontrado no 'spec' do SR cluster no ambiente {environment_id}.")
                else:
                    print(
                        f"Aviso: 'spec' ausente ou não é um dicionário para o SR cluster no ambiente {environment_id}.")
        else:
            print(
                f"Nenhum Schema Registry cluster encontrado no environment {environment_id} ou resposta da API inválida.")
    return sr_clusters_info


def get_schema_subjects(sr_clusters_info):
    subjects = []
    for sr_endpoint, environment_id, sr_cluster_id in sr_clusters_info:
        subjects_endpoint = f"{sr_endpoint}/subjects"
        subjects_response = make_api_request("GET", subjects_endpoint, environment_id=environment_id)

        if subjects_response and isinstance(subjects_response, list):
            subjects.extend(subjects_response)
        else:
            print(f"Nenhum subject encontrado no Schema Registry cluster {sr_cluster_id} ou resposta da API inválida.")
    return subjects


def get_role_bindings_for_principal_and_pattern(service_account_id: str, crn_pattern: str) -> list:
    endpoint = f"{API_BASE_URL}/iam/v2/role-bindings"
    params = {
        "principal": f"User:{service_account_id}",
        "crn_pattern": crn_pattern
    }
    response_data = make_api_request("GET", endpoint, params=params)

    if not response_data or 'data' not in response_data:
        return []

    return response_data.get('data', [])


def get_all_relevant_role_bindings(
        service_account_ids: list,
        organization_ids: list,
        environment_ids: list,
        kafka_clusters_info: list,
        kafka_topic_names: list,
        sr_clusters_info: list,
        sr_subject_names: list,
) -> list:
    all_unique_bindings = {}

    for sa_id in service_account_ids:
        print(f"\n--- Processando Service Account: {sa_id} ---")

        for org_id in organization_ids:
            org_crn_pattern = f"crn://confluent.cloud/organization={org_id}"
            bindings = get_role_bindings_for_principal_and_pattern(sa_id, org_crn_pattern)
            for binding in bindings:
                all_unique_bindings[binding['id']] = binding

            for env_id in environment_ids:
                env_crn_pattern = f"crn://confluent.cloud/organization={org_id}/environment={env_id}"
                bindings = get_role_bindings_for_principal_and_pattern(sa_id, env_crn_pattern)
                for binding in bindings:
                    all_unique_bindings[binding['id']] = binding

                for kafka_cid, kafka_env_id in kafka_clusters_info:
                    if kafka_env_id != env_id:
                        continue

                    kafka_cluster_patterns = [
                        f"crn://confluent.cloud/organization={org_id}/environment={env_id}/cloud-cluster={kafka_cid}/kafka={kafka_cid}"
                    ]
                    for pattern in kafka_cluster_patterns:
                        bindings = get_role_bindings_for_principal_and_pattern(sa_id, pattern)
                        for binding in bindings:
                            all_unique_bindings[binding['id']] = binding

                    for topic_name in kafka_topic_names:
                        kafka_topic_patterns = [
                            f"crn://confluent.cloud/organization={org_id}/environment={env_id}/cloud-cluster={kafka_cid}/kafka={kafka_cid}/topic={topic_name}"
                        ]
                        for pattern in kafka_topic_patterns:
                            bindings = get_role_bindings_for_principal_and_pattern(sa_id, pattern)
                            for binding in bindings:
                                all_unique_bindings[binding['id']] = binding

                for sr_endpoint, sr_env_id, sr_cluster_id in sr_clusters_info:
                    if sr_env_id != env_id:
                        continue

                    for subject_name in sr_subject_names:
                        sr_subject_pattern = f"crn://confluent.cloud/organization={org_id}/environment={env_id}/schema-registry={sr_cluster_id}/subject={subject_name}"
                        bindings = get_role_bindings_for_principal_and_pattern(sa_id, sr_subject_pattern)
                        for binding in bindings:
                            all_unique_bindings[binding['id']] = binding

    return list(all_unique_bindings.values())


if __name__ == "__main__":
    print(f"Iniciando busca de recursos...")
    print("--- Estágio 1: Descoberta de IDs de Recursos ---")

    organization_ids = get_organizations()
    print("\nIDs de Organizações:", organization_ids)

    environment_ids = get_environments()
    print("\nIDs de Ambientes:", environment_ids)

    kafka_clusters_info = get_clusters(environment_ids)
    print("\nId de Clusters", kafka_clusters_info)

    service_account_ids = get_service_accounts()
    print("\nIDs de Service Accounts:", service_account_ids)

    kafka_topic_names = get_topics(kafka_clusters_info)
    print("\nNomes de Tópicos Kafka:", kafka_topic_names)

    sr_clusters_info = get_schema_registry_clusters_endpoints(environment_ids)
    print("\nClusters Schema:", sr_clusters_info)

    sr_subject_names = get_schema_subjects(sr_clusters_info)
    print("\nSubjects do Schema Registry:", sr_subject_names)

    print("\n--- Estágio 2: Buscando e Agregando Role Bindings para Service Accounts ---")

    all_found_bindings = get_all_relevant_role_bindings(
        service_account_ids=service_account_ids,
        organization_ids=organization_ids,
        environment_ids=environment_ids,
        kafka_clusters_info=kafka_clusters_info,
        kafka_topic_names=kafka_topic_names,
        sr_clusters_info=sr_clusters_info,
        sr_subject_names=sr_subject_names
    )

    # print(f"\nTotal de {len(all_found_bindings)} role bindings únicos encontrados em todos os níveis.")
    # print("\n--- Detalhes dos Role Bindings Encontrados ---")
    # if all_found_bindings:
    #     for i, binding in enumerate(all_found_bindings[:5]):
    #         print(f"Binding {i + 1}:")
    #         print(json.dumps(binding, indent=2))
    #         print("-" * 50)
    #     if len(all_found_bindings) > 5:
    #         print(f"... e mais {len(all_found_bindings) - 5} bindings.")
    # else:
    #     print("Nenhum role binding encontrado com os critérios fornecidos.")

    print("\n--- Resumo das Roles e Recursos ---")
    resource_roles_map = {}
    for binding in all_found_bindings:
        resource = binding.get('resource')
        role_name = binding.get('role_name')
        principal = binding.get('principal')

        if resource not in resource_roles_map:
            resource_roles_map[resource] = []
        resource_roles_map[resource].append(f"SA: {principal.split(':')[-1]} - Role: {role_name}")

    for resource, roles_info in resource_roles_map.items():
        for role_info in roles_info:
            print(f"  - {role_info}")