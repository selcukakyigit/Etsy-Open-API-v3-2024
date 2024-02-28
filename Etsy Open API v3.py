import json
import requests
import webbrowser
import pkce

client_id = "Enter your clint id here."
client_secret = 'Enter your clint secret key here.'
redirect_url = 'https://www.example.com/some/location' #demo redirect urls
scope = 'transactions_r%20transactions_w'
code_verifier = pkce.generate_code_verifier(length=128)
code_challenge = pkce.get_code_challenge(code_verifier)

def EtsyFirstAuth():
    auth_url = f"https://www.etsy.com/oauth/connect?response_type=code&redirect_uri={redirect_url}&scope={scope}&client_id={client_id}&state=superstate&code_challenge={code_challenge}&code_challenge_method=S256"
    webbrowser.open_new(auth_url)

    auth_res_url = input('URL ==  ')
    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&state')
    auth_code = auth_res_url[start_number:end_number]
    print(auth_code)
    print('\n')

    return auth_code

def RefreshTokens(refresh_token):
    refresh_token_url = 'https://api.etsy.com/v3/public/oauth/token'
    response = requests.post(refresh_token_url,
                             headers={
                                 'Content-Type': 'application/x-www-form-urlencoded'
                             },
                             data={
                                 'grant_type': 'refresh_token',
                                 'client_id': client_id,
                                 'client_secret': client_secret,
                                 'refresh_token': refresh_token
                             })
    json_response = response.json()

    new_access_token = json_response['access_token']
    new_refresh_token = json_response['refresh_token']

    rt_file = open('refresh_token.txt', 'w')
    rt_file.write(new_refresh_token)
    rt_file.close()

    return [new_access_token, new_refresh_token]

def EtsyTenants(access_token):
    connections_url = "https://openapi.etsy.com/v3/application/shops/25333094/receipts"
    response = requests.get(connections_url,
                            headers={
                                'x-api-key': client_id,
                                'Authorization': 'Bearer ' + access_token,
                                'Content-Type': 'application/json'
                            })

    json_response = response.json()

    buyer_emails = []

    for result in json_response["results"]:
        name = result["name"]
        buyer_email = result["buyer_email"]
        sku = None
        formatted_address = result["formatted_address"]

        transactions = result["transactions"]
        for transaction in transactions:
            if "sku" in transaction:
                sku = transaction["sku"]
                break

        buyer_emails.append((name, buyer_email, sku, formatted_address))

    buyer_emails_one_line = " ".join(
        [f"{buyer_email} - {name} - {sku} - {formatted_address}" for name, buyer_email, sku, formatted_address in
         buyer_emails])

    for name, buyer_email, sku, formatted_address in buyer_emails:
        print(f"Name: {name}")
        print(f"Buyer Email: {buyer_email}")
        print(f"Sku: {sku}")
        print(f"Customer Address: {formatted_address}")
        print()

def CallAPI():
    old_refresh_token = open('refresh_token.txt', 'r').read()
    new_tokens = RefreshTokens(old_refresh_token)
    access_token = new_tokens[0]
    EtsyTenants(access_token)

    get_url = "https://openapi.etsy.com/v3/application/shops/25333094/receipts"
    response = requests.get(get_url,
                            headers={
                                'x-api-key': client_id,
                                'Authorization': 'Bearer ' + access_token,
                                'Content-Type': 'application/json'
                            })
    json_response = response.json()
    formatted_json = json.dumps(json_response, indent=4)  # JSON verisini düzenli bir şekilde formatlayarak yazdırma
    #print(formatted_json)

    xero_output = open('callAPI_Bel.txt', 'w')
    xero_output.write(formatted_json)
    xero_output.close()


def XeroRequests():
    auth_code = EtsyFirstAuth()
    exchange_code_url = 'https://api.etsy.com/v3/public/oauth/token'
    response = requests.post(exchange_code_url,
                             headers={
                                 'Content-Type': 'application/x-www-form-urlencoded'
                             },
                             data={
                                 'grant_type': 'authorization_code',
                                 'client_id': client_id,
                                 'client_secret': client_secret,
                                 'redirect_uri': redirect_url,
                                 'code': auth_code,
                                 'code_verifier': code_verifier
                             })
    json_response = response.json()

    old_refresh_token = json_response.get('refresh_token')
    new_tokens = RefreshTokens(old_refresh_token)
    access_token = new_tokens[0]
    new_refresh_token = new_tokens[1]

    # İlk kez EtsyTenants fonksiyonunu çağırma
    EtsyTenants(access_token)

    # Yenilenmiş refresh_token'ı kullanarak token yenileme
    new_tokens = RefreshTokens(new_refresh_token)
    access_token = new_tokens[0]
    new_refresh_token = new_tokens[1]

    # Yenilenmiş erişim belirteciyle işlemlere devam etme
    CallAPI()

XeroRequests() #Call this function for initial authorization.
#CallAPI()