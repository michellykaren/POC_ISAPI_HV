import os
import requests
from requests.auth import HTTPDigestAuth
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET

"""
Sobre os Parâmetros  
- Se o valor fornecido for maior que o máximo permitido, será definido como o valor máximo.  
- Se o valor fornecido for menor que o mínimo permitido, será definido como 0.  
- Se um valor inválido for enviado (letras ou formato incorreto), a resposta retornará badreq.  
- Se uma tag vazia for enviada, as configurações atuais serão mantidas.  
- Não é necessário enviar todas as tags internas. Exemplo: ao enviar apenas `<brightnessLevel>0</brightnessLevel>`, 
as demais configurações permanecerão inalteradas.  
"""

def verificar_camera_conectada(camera_ip, username, password):
    url = f'http://{camera_ip}/ISAPI/Security/UserPermission/1'
    
    try:
        response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=5)
        
        if response.status_code == 200:
            print(f'Conexão com a câmera {camera_ip} VALIDADA')
            return True
        elif response.status_code == 401:
            print(f'Conexão FALHOU para {camera_ip}: Login ou senha incorretos.')
            return False
        else:
            print(f'Conexão FALHOU para {camera_ip}: Erro desconhecido (Código de status: {response.status_code})')
            return False

    except requests.exceptions.Timeout:
        print(f'Conexão FALHOU para {camera_ip}: Tempo limite excedido ao tentar conectar à câmera.')
        return False
    except requests.exceptions.RequestException as e:
        print(f'Conexão FALHOU para {camera_ip}: Erro de conexão - {e}')
        return False

def salvar_xml_conteudo(conteudo_xml, nome_arquivo):
    # Faz o parse do conteúdo XML para indentá-lo com menos quebras de linha
    xml_dom = parseString(conteudo_xml)
    xml_pretty_str = "\n".join([line for line in xml_dom.toprettyxml(indent="    ").splitlines() if line.strip()])
    
    # Salva o XML formatado sem quebras de linha extras
    with open(nome_arquivo, "w", encoding="utf-8") as file:
        file.write(xml_pretty_str)
    print(f"Conteúdo XML salvo com sucesso em '{nome_arquivo}' com indentação reduzida.")

def get_parametros_imagem(camera_ip, username, password, output_file="get_image_parameters_1027_defaul_conf.xml"):
    # Primeiro, verifica se a câmera está conectada
    if not verificar_camera_conectada(camera_ip, username, password):
        return
    
    #url = f'http://{camera_ip}/ISAPI/Image/channels' /ISAPI/Image/channels
    url = f'http://{camera_ip}/ISAPI/Image/channels'
    
    try:
        # Envia a requisição GET com autenticação Digest
        response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Salva o conteúdo XML usando a função salvar_xml_conteudo
            salvar_xml_conteudo(response.content, output_file)
        else:
            print(f"Falha ao obter parâmetros de imagem. Código de status: {response.status_code}")
            print("Conteúdo da resposta:", response.text)

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")

def set_parametros_imagem(camera_ip, username, password, xml_file="put_display_settings.xml"):
    
    url = f'http://{camera_ip}/ISAPI/Image/channels'
    
    # Lê o conteúdo do arquivo XML
    with open(xml_file, "rb") as file:
        xml_data = file.read()

    # Define os cabeçalhos para o envio do XML
    headers = {
        'Content-Type': 'application/xml'
    }

    try:
        # Envia a requisição PUT com o XML e autenticação Digest
        response = requests.put(url, data=xml_data, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Parse da resposta para verificar o status de retorno
            response_xml = response.content.decode("utf-8")
            if "<statusCode>0</statusCode>" in response_xml and "<statusString>OK</statusString>" in response_xml:
                print("Parâmetros de imagem configurados com sucesso.")
                return 0
            else:
                print("Falha ao configurar os parâmetros de imagem: resposta inesperada.")
                print("Conteúdo da resposta:", response_xml)
                return -1
        else:
            print(f"Erro ao configurar parâmetros de imagem. Código de status HTTP: {response.status_code}")
            return -1

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
        return -1
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")
        return -1

def set_image_adjustment(camera_ip, username, password, channel_id=1):
    color_url = f'http://{camera_ip}/ISAPI/Image/channels/{channel_id}/color'
    sharpness_url = f'http://{camera_ip}/ISAPI/Image/channels/{channel_id}/sharpness'
    
    # XML com brilho, contraste e saturação
    color_xml = '''<?xml version="1.0" encoding="UTF-8"?><Color>
    <brightnessLevel>35</brightnessLevel>
    <contrastLevel>35</contrastLevel>
    <saturationLevel>35</saturationLevel></Color>'''

    # XML para nitidez
    sharpness_xml = '''<?xml version="1.0" encoding="UTF-8"?><Sharpness xmlns="http://www.isapi.org/ver20/XMLSchema" version="2.0">
    <SharpnessLevel>15</SharpnessLevel></Sharpness>'''

    headers = {
        'Content-Type': 'application/xml'
    }

    try:
        color_response = requests.put(color_url, data=color_xml, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)
        
        # Verifica se a configuração de cor foi bem-sucedida
        if color_response.status_code == 200:
            color_response_xml = color_response.content.decode("utf-8")
            if "<statusCode>1</statusCode>" in color_response_xml and "<statusString>OK</statusString>" in color_response_xml:
                print("Parâmetros de cor configurados com sucesso.")
                print("Conteúdo da resposta:", color_response_xml)
            else:
                print("Falha ao configurar os parâmetros de cor: resposta inesperada.")
                print("Conteúdo da resposta:", color_response_xml)
                return -1
        else:
            print(f"Erro ao configurar parâmetros de cor. Código de status HTTP: {color_response.status_code}")
            return -1

        # Envia a requisição PUT para configuração de nitidez
        sharpness_response = requests.put(sharpness_url, data=sharpness_xml, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a configuração de nitidez foi bem-sucedida
        if sharpness_response.status_code == 200:
            sharpness_response_xml = sharpness_response.content.decode("utf-8")
            if "<statusCode>1</statusCode>" in sharpness_response_xml and "<statusString>OK</statusString>" in sharpness_response_xml:
                print("Parâmetros de nitidez configurados com sucesso.")
                print("Conteúdo da resposta:", sharpness_response_xml)
                return 0
            else:
                print("Falha ao configurar os parâmetros de nitidez: resposta inesperada.")
                print("Conteúdo da resposta:", sharpness_response_xml)
                return -1
        else:
            print(f"Erro ao configurar parâmetros de nitidez. Código de status HTTP: {sharpness_response.status_code}")
            return -1

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
        return -1
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")
        return -1

def get_exposure_mode(camera_ip, username, password, channel_id=1, parameter_type="exposureMode"):
    # URL para obter o modo de exposição de um canal específico
    url = f'http://{camera_ip}/ISAPI/Image/channels/{channel_id}/exposure?parameterType={parameter_type}'

    try:
        # Envia a requisição GET para obter o modo de exposição
        response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a requisição foi bem-sucedida e exibe a resposta
        if response.status_code == 200:
            print("Modo de exposição obtido com sucesso.")
            print("Resposta XML:")
            print(response.text)  # Imprime a resposta XML
        else:
            print(f"Erro ao obter o modo de exposição. Código de status HTTP: {response.status_code}")
            print("Conteúdo da resposta:", response.text)

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")

def get_shutter_time_levels_from_file(camera_ip, username, password, file_path="get_image_parameters.xml"):
    # Verifica se o arquivo XML existe na raiz do projeto
    if not os.path.exists(file_path):
        print(f"Arquivo '{file_path}' não encontrado. Obtendo da câmera...")
        get_parametros_imagem(camera_ip, username, password, output_file=file_path)

    try:
        # Carrega e parseia o arquivo XML
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Busca pelo elemento ShutterLevel e obtém o atributo 'opt' com as opções
        shutter_level = root.find(".//{http://www.hikvision.com/ver20/XMLSchema}ShutterLevel")
        
        if shutter_level is not None:
            shutter_options = shutter_level.get("opt")
            if shutter_options:
                shutter_levels = shutter_options.split(",")
                return shutter_levels
            else:
                print("Nenhuma opção de ShutterLevel encontrada.")
                return []
        else:
            print("Elemento ShutterLevel não encontrado no XML.")
            return []

    except ET.ParseError:
        print("Erro ao parsear o XML.")
        return []
    except FileNotFoundError:
        print("Arquivo de parâmetros de imagem não encontrado.")
        return []

def set_gain_level(camera_ip, username, password, channel_id=1, gain_level=40):
    # Define a URL do endpoint para configurar o nível de ganho
    url = f'http://{camera_ip}/ISAPI/Image/channels/{channel_id}/gain'
    
    # XML para configuração do nível de ganho
    gain_xml = f'''<?xml version="1.0" encoding="UTF-8"?><Gain xmlns="http://www.hikvision.com/ver20/XMLSchema" version="2.0">
    <GainLevel>{gain_level}</GainLevel></Gain>'''

    # Define os cabeçalhos para o envio do XML
    headers = {
        'Content-Type': 'application/xml'
    }

    try:
        # Envia a requisição PUT para configurar o nível de ganho
        response = requests.put(url, data=gain_xml, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a configuração de ganho foi bem-sucedida
        if response.status_code == 200:
            response_xml = response.content.decode("utf-8")
            if "<statusCode>1</statusCode>" in response_xml and "<statusString>OK</statusString>" in response_xml:
                print("Parâmetro de ganho configurado com sucesso.")
                return "SUCCESS"
            else:
                print("Falha ao configurar o ganho: resposta inesperada.")
                print("Conteúdo da resposta:", response_xml)
                return "ERROR"
        else:
            print(f"Erro ao configurar o ganho. Código de status HTTP: {response.status_code}")
            return "ERROR"

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
        return "ERROR"
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")
        return "ERROR"

def set_white_balance(camera_ip, username, password, channel_id=1, white_balance_style="auto1", white_balance_red=None, white_balance_blue=None):
    #o modo manual só funciona para cameras com esse suporte, por exemplo a de 4MP usada
    #a opção tem que ser escrita certinha, por exemplo o daylightLamp tem o L maiusculo, eles não tratam outros casos
    # Define a URL do endpoint para configurar o balanço de branco
    url = f'http://{camera_ip}/ISAPI/Image/channels/{channel_id}/whiteBalance'
    
    # Monta o XML para configuração do balanço de branco
    # Inclui WhiteBalanceRed e WhiteBalanceBlue somente se o estilo for "manual"
    if white_balance_style == "manual" and white_balance_red is not None and white_balance_blue is not None:
        white_balance_xml = f'''<?xml version="1.0" encoding="UTF-8"?><WhiteBalance xmlns="http://www.hikvision.com/ver20/XMLSchema" version="2.0">
    <WhiteBalanceStyle>{white_balance_style}</WhiteBalanceStyle>
    <WhiteBalanceRed>{white_balance_red}</WhiteBalanceRed>
    <WhiteBalanceBlue>{white_balance_blue}</WhiteBalanceBlue></WhiteBalance>'''
    else:
        white_balance_xml = f'''<?xml version="1.0" encoding="UTF-8"?><WhiteBalance xmlns="http://www.hikvision.com/ver20/XMLSchema" version="2.0">
    <WhiteBalanceStyle>{white_balance_style}</WhiteBalanceStyle></WhiteBalance>'''

    # Define os cabeçalhos para o envio do XML
    headers = {
        'Content-Type': 'application/xml'
    }

    try:
        # Envia a requisição PUT para configurar o balanço de branco
        response = requests.put(url, data=white_balance_xml, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a configuração de balanço de branco foi bem-sucedida
        if response.status_code == 200:
            response_xml = response.content.decode("utf-8")
            if "<statusCode>1</statusCode>" in response_xml and "<statusString>OK</statusString>" in response_xml:
                print("Parâmetro de balanço de branco configurado com sucesso.")
                return "SUCCESS"
            else:
                print("Falha ao configurar o balanço de branco: resposta inesperada.")
                print("Conteúdo da resposta:", response_xml)
                return "ERROR"
        else:
            print(f"Erro ao configurar o balanço de branco. Código de status HTTP: {response.status_code}")
            return "ERROR"

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
        return "ERROR"
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")
        return "ERROR"

def set_shutter(camera_ip, username, password, channel_id=1, shutter_level="1/1"):
    #Se é colocado algum valor de shutter fora da lista de opções temos err 400 sempre pegar a lista de valores possíveis antes
    # URL para configurar o obturador do canal especificado
    url = f'http://{camera_ip}/ISAPI/Image/channels/{channel_id}/shutter'
    
    # XML para configuração do nível de obturador
    shutter_xml = f'''<?xml version="1.0" encoding="UTF-8"?><Shutter xmlns="http://www.isapi.org/ver20/XMLSchema" version="2.0">
    <ShutterLevel>{shutter_level}</ShutterLevel></Shutter>'''

    # Define os cabeçalhos para o envio do XML
    headers = {
        'Content-Type': 'application/xml'
    }

    try:
        # Envia a requisição PUT para configuração do obturador
        response = requests.put(url, data=shutter_xml, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a configuração de obturador foi bem-sucedida
        if response.status_code == 200:
            response_xml = response.content.decode("utf-8")
            if "<statusCode>1</statusCode>" in response_xml and "<statusString>OK</statusString>" in response_xml:
                print("Parâmetro de obturador configurado com sucesso.")
                return 0
            else:
                print("Falha ao configurar o obturador: resposta inesperada.")
                print("Conteúdo da resposta:", response_xml)
                return -1
        else:
            print(f"Erro ao configurar o obturador. Código de status HTTP: {response.status_code}")
            return -1

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
        return -1
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")
        return -1

def set_ircut(camera_ip, username, password, channel_id=1, ircut_filter_type="day"):
    # URL para configurar o IrcutFilter do canal especificado
    url = f'http://{camera_ip}/ISAPI/Image/channels/{channel_id}/ircutFilter'

    # XML para configuração do tipo de filtro IR-cut
    ircut_xml = f'''<?xml version="1.0" encoding="UTF-8"?><IrcutFilter xmlns="http://www.hikvision.com/ver20/XMLSchema" version="2.0">
    <IrcutFilterType>{ircut_filter_type}</IrcutFilterType></IrcutFilter>'''

    # Define os cabeçalhos para o envio do XML
    headers = {
        'Content-Type': 'application/xml'
    }

    try:
        # Envia a requisição PUT para configuração do IrcutFilter
        response = requests.put(url, data=ircut_xml, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a configuração foi bem-sucedida
        if response.status_code == 200:
            response_xml = response.content.decode("utf-8")
            if "<statusCode>1</statusCode>" in response_xml and "<statusString>OK</statusString>" in response_xml:
                print("Parâmetro IR-cut configurado com sucesso.")
                return 0
            else:
                print("Falha ao configurar IR-cut: resposta inesperada.")
                print("Conteúdo da resposta:", response_xml)
                return -1
        else:
            print(f"Erro ao configurar IR-cut. Código de status HTTP: {response.status_code}")
            return -1

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar cosnectar à câmera {camera_ip}.")
        return -1
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")
        return -1

camera_ip = ""
username = ""
password = ""

#get_exposure_mode(camera_ip, username, password, channel_id=1, parameter_type="exposureMode")
#get_shutter_options(camera_ip, username, password, channel_id=1)

#shutter_levels = get_shutter_time_levels_from_file(camera_ip, username, password)
#if shutter_levels:
    #print("Lista de níveis de obturador disponíveis:", shutter_levels)

#status = set_shutter(camera_ip, username, password, shutter_level="1/120")
#status = set_ircut(camera_ip, username, password, ircut_filter_type="day");
#status = set_gain_level(camera_ip, username, password, channel_id=1, gain_level=40)
#status = get_parametros_imagem(camera_ip, username, password)
#status = set_white_balance(camera_ip, username, password, channel_id=1, white_balance_style="daylightLamp") 
#status = set_white_balance(camera_ip, username, password, channel_id=1, white_balance_style="manual", white_balance_red=60, white_balance_blue=70)

if (status == "SUCCESS" or status == 0):
    print("Parâmetro configurado com sucesso.")
else:
    print("Falha ao configurar parâmetro")


