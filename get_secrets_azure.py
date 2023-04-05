import os
import sys
import requests

def get_secrets_from_azure(secret_keys, tags):
    # Authenticate with Azure
    tenant_id = os.environ.get('AZURE_TENANT_IDS')
    client_id = os.environ.get('AZURE_CLIENT_IDS')
    client_secret = os.environ.get('AZURE_CLIENT_SECRETS')
    resource = 'https://vault.azure.net'
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': resource
    }
    response = requests.post(url, data=data).json()

    # Retrieve the list of secrets from Azure Key Vault
    vault_name = os.environ.get('AZURE_KEY_VAULT_NAME')
    url = f"https://{vault_name}.vault.azure.net/secrets?api-version=2016-10-01"
    headers = {
        'Authorization': f"Bearer {response['access_token']}"
    }
    response = requests.get(url, headers=headers).json()
    secret_values = {}

    # Filter the list of secrets to include only those with keys in secret_keys
    secrets = response['value']
    if secret_keys:
        filtered_secrets = [secret for secret in secrets if secret['id'].split('/')[-1] in secret_keys]
    # Retrieve the values of the filtered secrets
        for secret in filtered_secrets:
            secret_name = secret['id'].split('/')[-1]
            url = f"https://{vault_name}.vault.azure.net/secrets/{secret_name}?api-version=2016-10-01"
            response = requests.get(url, headers=headers).json()
            secret_values[secret_name] = response['value']

      # Filter the list of secrets to include only those with keys in tags
    if tags:
        multiple_tags=[]
        for tag in tags:
            tag_key = tag.split('=')[0]
            tag_value = tag.split('=')[1]
            filter = [x for x in secrets if x['tags'].get(tag_key) == tag_value]
            for item in filter:
                secret_name_tag = item['id'].split('/')[-1]
                #If the secrets has multiple tags and it is already picked
                if secret_name_tag in multiple_tags:
                    continue
                multiple_tags.append(secret_name_tag)
                #Get secrets values
                url = f"https://{vault_name}.vault.azure.net/secrets/{secret_name_tag}?api-version=2016-10-01"
                response = requests.get(url, headers=headers).json()
                secret_values[secret_name_tag] = response['value']
    return secret_values

if __name__ == '__main__':
    # Retrieve the list of secret keys from command line arguments
    secret_keys = sys.argv[1].split(',')
    # Retrieve the list of secret tags from command line arguments
    tags = sys.argv[2].split(',')
    # Retrieve the secret values from Azure Key Vault
    secret_values = get_secrets_from_azure(secret_keys, tags)

    # Output the secret values into a artifact file
    with open('shared_vars.sh', 'w') as f:
        for key, value in secret_values.items():
            f.write(f'export {key}={value}\n')