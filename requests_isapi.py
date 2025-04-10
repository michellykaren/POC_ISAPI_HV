import os
import requests
from requests.auth import HTTPDigestAuth
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
import time
import base64 

"""
Sobre as requisições no geral
- Se o valor fornecido for maior que o máximo permitido, será definido como o valor máximo.  
- Se o valor fornecido for menor que o mínimo permitido, será definido como 0.  
- Se um valor inválido for enviado (letras ou formato incorreto), a resposta retornará badreq.  
- Se uma tag vazia for enviada, as configurações atuais serão mantidas.  
- Não é necessário enviar todas as tags internas. Exemplo: ao enviar apenas `<brightnessLevel>0</brightnessLevel>`, 
as demais configurações permanecerão inalteradas. 
- Tanto as tags quanto os payload são casesensitive
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

def salvar_imagem(camera_ip, username, password):
    url = f"http://{camera_ip}/ISAPI/Streaming/channels/1/picture"
    filename = f"{camera_ip}_imagem.jpg"
    try:
        response = requests.get(url, auth=HTTPDigestAuth(username, password), stream=True)
        if response.status_code == 200:
            with open(filename, "wb") as file:
                file.write(response.content)
            print(f"Captura de imagem para {camera_ip} validada. Imagem salva como {filename}")
        else:
            print(f"Captura de imagem falhou para {camera_ip}. Código de status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Captura de imagem falhou para {camera_ip}. Erro de conexão: {e}")

def fps_captura_imagem(camera_ip, username, password, n=500):
  url = f"http://{camera_ip}/ISAPI/Streaming/channels/1/picture"
  tempos = []

  for i in range(n):
    OUTPUT_FILE = f"{camera_ip}_{i}_snapshot.jpg"
    start_time = time.perf_counter()
    
    try:
      response = requests.get(url, auth=HTTPDigestAuth(username, password), stream=True)
      tempos.append(time.perf_counter() - start_time)
      if response.status_code == 200:
        with open(OUTPUT_FILE, "wb") as file:
          file.write(response.content)
          print("Tudo certo!")
              
    except requests.RequestException:
      print("Deu merda")

  if tempos:
    fps_min = 1 / max(tempos)
    fps_max = 1 / min(tempos)
    fps_medio = 1 / (sum(tempos) / len(tempos))

    print(f"{fps_min:.4f} {fps_max:.4f} {fps_medio:.4f}")

def get_parametros_imagem(camera_ip, username, password, output_file="get_image_parameters_7a46_defaul_conf.xml"):
    """ 
    Exemplo resposta, não tem as opções de input
    <ImageChannel>
        <id>1</id>
        <enabled>true</enabled>
        <videoInputID>1</videoInputID>
        <ImageFlip xmlns="http://www.hikvision.com/ver20/XMLSchema" version="2.0">
            <enabled>false</enabled>
        </ImageFlip>
        <WDR xmlns="http://www.hikvision.com/ver20/XMLSchema" version="2.0">
            <enabled>false</enabled>
            <WDRLevel>67</WDRLevel>
        </WDR> ... brilho, contraste, todas as configs de display
    """
    # Primeiro, verifica se a câmera está conectada
    if not verificar_camera_conectada(camera_ip, username, password):
        return
    
    url = f'http://{camera_ip}/ISAPI/Image/channels'
    
    try:
        # Envia a requisição GET com autenticação Digest
        response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Salva o conteúdo XML usando a função salvar_xml_conteudo
            print(response.text)
            salvar_xml_conteudo(response.content, output_file)
        else:
            print(f"Falha ao obter parâmetros de imagem. Código de status: {response.status_code}")
            print("Conteúdo da resposta:", response.text)

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")

def get_system_capacities(camera_ip, username, password, output_file="get_system_capacities_4A24_defaul_conf.xml"):
    """ 
    Exemplo resposta
    <DeviceCap>
        <isSupportROI>true</isSupportROI>
        <isSupportX>true</isSupportX>
    </DeviceCap>
    """
   
    url = f'http://{camera_ip}/ISAPI/System/capabilities'
    
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

def get_device_status_capacities(camera_ip, username, password, output_file="get_system_status_7a46_defaul_conf.xml"):
    """
    Exemplo resposta
    <DeviceStatus>
        <currentDeviceTime>2011-01-01T22:35:52-03:00</currentDeviceTime>
        <deviceUpTime>81387</deviceUpTime>
        <CPUList>
        ...
        </CPUList>
        <MemoryList>
        ...
        </MemoryList>
    </DeviceStatus>
    """
   
    url = f'http://{camera_ip}/ISAPI/System/status'
    
    try:
        # Envia a requisição GET com autenticação Digest
        response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=5)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Salva o conteúdo XML usando a função salvar_xml_conteudo
            print(response.text)
            salvar_xml_conteudo(response.content, output_file)
        else:
            print(f"Falha ao obter parâmetros de status. Código de status: {response.status_code}")
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

def get_image_capabilities(camera_ip, username, password, output_file="get_image_capabilities.xml", ca_cert_path="/etc/ssl/certs/hikvision_2048_cert.pem"):
    url = f'https://{camera_ip}/ISAPI/Image/channels/1/capabilities'  # Note o https

    # Se não passar o caminho do certificado, usará o padrão do sistema
    verify_ssl = ca_cert_path if ca_cert_path else True

    try:
        response = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=5, verify=false)

        if response.status_code == 200:
            salvar_xml_conteudo(response.content, output_file)
            print(f"Capabilities salvas em {output_file}")
        else:
            print(f"Falha ao obter capabilities. Status: {response.status_code}")
            print(response.text)
    except requests.exceptions.SSLError as ssl_err:
        print(f"Erro de SSL: {ssl_err}")
    except requests.exceptions.Timeout:
        print(f"Timeout ao conectar com {camera_ip}")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")

def set_distorcao_lente(camera_ip, username, password, enabled=True):
    """
    Envia requisição PUT para habilitar ou desabilitar correção de distorção de lente.
    """
    url = f'http://{camera_ip}/ISAPI/Image/channels/1/lensDistortionCorrection'
    headers = {'Content-Type': 'application/xml'}

    payload = f"""
    <LensDistortionCorrection>
        <enabled>{"true" if enabled else "false"}</enabled>
    </LensDistortionCorrection>
    """.strip()

    try:
        response = requests.put(url, data=payload, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)

        if response.status_code == 200:
            print(f"Distorção de lente {'habilitada' if enabled else 'desabilitada'} com sucesso!")
            return 0
        else:
            print(f"Falha ao ajustar distorção de lente. Código de status: {response.status_code}")
            print(f"Resposta: {response.text}")

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")
    return -1

def set_eis(camera_ip, username, password, enabled=True):
    """
    Ativa ou desativa a estabilização eletrônica de imagem (EIS) na câmera Hikvision.
    """
    url = f'http://{camera_ip}/ISAPI/Image/channels/1/EIS'
    headers = {'Content-Type': 'application/xml'}

    payload = f"""
    <EIS>
        <enabled>{"true" if enabled else "false"}</enabled>
    </EIS>
    """.strip()

    try:
        response = requests.put(url, data=payload, headers=headers, auth=HTTPDigestAuth(username, password), timeout=5)

        if response.status_code == 200:
            print(f"EIS {'ativado' if enabled else 'desativado'} com sucesso!")
        else:
            print(f"Falha ao configurar EIS. Código de status: {response.status_code}")
            print("Resposta:", response.text)

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")

def set_exposure_by_modes(camera_ip, username, password, modo, iris_level=None):
    """
    Ajusta a exposição da câmera Hikvision via ISAPI, com 3 modos definidos:
    - "manual"
    - "p-iris-auto"
    - "p-iris-manual" (com iris_level opcional, padrão 40)
    """

    url = f'http://{camera_ip}/ISAPI/Image/channels/1/exposure'
    headers = {'Content-Type': 'application/xml'}

    # Valida o modo
    modos_validos = ["manual", "p-iris-auto", "p-iris-manual"]
    if modo not in modos_validos:
        raise ValueError(f"Modo inválido. Escolha entre: {', '.join(modos_validos)}")
    # Define valor padrão para iris_level no modo p-iris-manual
    if modo == "p-iris-manual" and iris_level is None:
        iris_level = 40
    # Monta o XML usando ET (ElementTree)
    exposure = ET.Element('Exposure')
    # Define ExposureType
    exposure_type_elem = ET.SubElement(exposure, 'ExposureType')
    # Adiciona os campos comuns a todos os modos
    #overexpose = ET.SubElement(exposure, 'OverexposeSuppress')Se eu não enviar o parâmetro de exposição ainda dá certo
    #ET.SubElement(overexpose, 'enabled').text = 'false'

    # Configuração por modo
    if modo == "manual":
        exposure_type_elem.text = "manual"

    elif modo == "p-iris-auto":
        exposure_type_elem.text = "pIris-General"
        piris_general = ET.SubElement(exposure, 'PIrisGeneral')
        ET.SubElement(piris_general, 'pIrisType').text = "auto"

    elif modo == "p-iris-manual":
        exposure_type_elem.text = "pIris-General"
        piris_general = ET.SubElement(exposure, 'PIrisGeneral')
        ET.SubElement(piris_general, 'pIrisType').text = "MANUAL"
        ET.SubElement(piris_general, 'irisLevel').text = str(iris_level)

    # Converte o XML para string
    payload = ET.tostring(exposure, encoding='unicode')

    try:
        response = requests.put(url, data=payload, headers=headers,
            auth=HTTPDigestAuth(username, password), timeout=5)

        if response.status_code == 200:
            print(f"Exposição ajustada com sucesso para o modo '{modo}'.")
            if modo == "p-iris-manual":
                print(f"Iris Level ajustado para {iris_level}")
        else:
            print(f"Falha ao ajustar exposição. Código de status: {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")

def get_color_config(camera_ip, username, password, https=False, cert_path="/etc/ssl/mobit.crt"):
    """
    Faz uma requisição GET para obter as configurações de cor da câmera Hikvision.
    Args:
        camera_ip (str): IP da câmera.
        username (str): Usuário.
        password (str): Senha.
        https (bool): Se True, usa HTTPS com verificação SSL; caso contrário, usa HTTP.
        cert_path (str): Caminho para o certificado SSL confiável (usado apenas se https=True).
    
    Return:
        str: Resposta XML das configurações de cor, ou None em caso de falha.
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Image/channels/1/color"
    headers = {'Content-Type': 'application/xml'}

    try:
        response = requests.get(
            url,
            headers=headers,
            auth=HTTPDigestAuth(username, password),
            verify=cert_path if https else False,
            timeout=5
        )

        if response.status_code == 200:
            print("Configurações de cor obtidas com sucesso!")
            print(response.text)
            return response.text
        else:
            print(f"Falha ao obter configurações de cor. Código de status: {response.status_code}")
            print(response.text)

    except requests.exceptions.SSLError as ssl_err:
        print(f"Erro de verificação SSL: {ssl_err}")
    except requests.exceptions.Timeout:
        print(f"Erro: Tempo limite excedido ao tentar conectar à câmera {camera_ip}.")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão com a câmera {camera_ip}: {e}")

##################### security function #########################

def get_security_capabilities(camera_ip, username, password, https=True, cert_path=None):
    """
    Requisição GET para /ISAPI/Security/capabilities de câmeras Hikvision. Printa os "isSupportX"
    Args:
        https (bool): Se True, usa HTTPS. Se False, usa HTTP.
        cert_path (str, optional): Caminho para o certificado (apenas se HTTPS for usado).
    Returns:
        dict | str: Resposta em JSON (se possível)
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Security/capabilities"

    try:
        if https and cert_path:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=cert_path,
                timeout=5
            )
        else:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=https,
                timeout=5
            )
        
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def get_certificate_select_capabilities(camera_ip, username, password, https=True, cert_path=None):
    """
    Requisição GET para /ISAPI/Security/certificate/select/capabilities?format=json

    Args:
        camera_ip (str): IP da câmera.
        username (str): Nome de usuário.
        password (str): Senha.
        https (bool): Se True, usa HTTPS. Se False, usa HTTP.
        cert_path (str, optional): Caminho do certificado (usado se HTTPS for True).
    Returns:
        dict | str: Resposta JSON (se possível)
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Security/certificate/select/capabilities?format=json"

    try:
        if https and cert_path:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=cert_path,
                timeout=5
            )
        else:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=https,
                timeout=5
            )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def get_device_certificate_capabilities(camera_ip, username, password, https=True, cert_path=None):
    """
    Requisição GET para /ISAPI/Security/deviceCertificate/capabilities?format=json
    para obter as capacidades que o sistema oferece (ver o opt basicamente)
    Args:
        https: Se True, usa HTTPS. Se False, usa HTTP.
        cert_path: Caminho do certificado (usado se HTTPS for True).
    Returns:
        dict | str: Resposta JSON (se possível) ou texto puro.
    Exemple:
        {'CertificateRevocationCap': {'customID': {'@min': 1, '@max': 64}, 'status': {'@opt': ['normal', 'expired', 'exceptional']}}},)
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Security/deviceCertificate/capabilities?format=json"

    try:
        if https and cert_path:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=cert_path,
                timeout=5
            )
        else:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=https,
                timeout=5
            )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def get_certificate_revocation_config(camera_ip, username, password, https=True, cert_path=None):
    """
    Requisição GET para /ISAPI/Security/certificate/certificateRevocation?format=json
    para obter configurações de revogação (expiração) de certificado.
    Args:
        https: Se True, usa HTTPS. Se False, usa HTTP.
        cert_path: Caminho do certificado confiável (usado se HTTPS for True).
    Returns:
        dict | str: Resposta JSON (se possível) ou texto puro.
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Security/deviceCertificate/certificateRevocation?format=json"

    try:
        if https and cert_path:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=cert_path,
                timeout=10
            )
        else:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=https,
                timeout=10
            )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def get_server_certificates(camera_ip, username, password, https=False, cert_path=None):
    """
    Requisição GET para /ISAPI/Security/serverCertificate/certificates?format=json
    O melhor para obter parâmetros de todos os certificados instalados. Equivalente as propriedades de certificado na interface.
    Args:
        https: Se True, usa HTTPS. Se False, usa HTTP.
        cert_path: Caminho do certificado confiável (usado se HTTPS for True).
    Returns:
        dict | str: Resposta JSON ou texto.
    Exemple:
        'CertificateInfo': [
        {
          'issuerDN': 'GeoTrustTLSRSACAG1',
          'subjectDN': '*.mobit.com.br',
          'startDate': '2024-11-0108: 00: 00',
          'endDate': '2025-11-0507: 59: 59',
          'type': 'HTTPS',
          'status': 'normal',
          'customID': 'mobitt1'
        }
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Security/serverCertificate/certificates?format=json"

    try:
        if https and cert_path:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=cert_path,
                timeout=10
            )
        else:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=https,
                timeout=10
            )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def delete_server_certificate(camera_ip, username, password, custom_id, https=False, cert_path=None):
    """
    Deleta um certificado do servidor usando o customID via ISAPI.

    Args:
        camera_ip (str): IP da câmera.
        username (str): Nome de usuário.
        password (str): Senha.
        custom_id (str): Identificador do certificado (ex: "mobitt1").
        https (bool): Se True, usa HTTPS.
        cert_path (str, optional): Caminho para o certificado confiável (opcional se HTTPS).

    Returns:
        bool: True se a exclusão foi bem-sucedida, False caso contrário.
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Security/serverCertificate/certificates/{custom_id}?format=json"

    try:
        if https and cert_path:
            response = requests.delete(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=cert_path,
                timeout=10
            )
        else:
            response = requests.delete(
                url,
                auth=HTTPDigestAuth(username, password),
                verify=https,
                timeout=10
            )

        print(f"Status code: {response.status_code}")
        return response.status_code == 200

    except requests.exceptions.RequestException as e:
        print(f"Erro ao deletar certificado: {e}")
        return False

def upload_server_certificate_with_iv(camera_ip, username, password, cert_file_path, custom_id, iv, https=False, cert_path=None):
    """
    Faz upload de certificado .pfx com chave privada para a câmera Hikvision via ISAPI,
    usando o IV capturado manualmente da interface da câmera.
    Args:
        camera_ip (str): IP da câmera.
        username (str): Usuário da câmera.
        password (str): Senha da câmera.
        cert_file_path (str): Caminho para o arquivo .pfx (PKCS#12).
        custom_id (str): Nome identificador do certificado.
        iv (str): Valor do IV capturado da interface (32 caracteres hex).
        https (bool): Se True, usa HTTPS.
        cert_path (str, optional): Caminho para o certificado confiável (em modo HTTPS).
    Returns:
        bool: True se o upload foi bem-sucedido, False caso contrário.
    """
    protocol = "https" if https else "http"
    url = (
        f"{protocol}://{camera_ip}/ISAPI/Security/serverCertificate/certificate"
        f"?customID={custom_id}"
    )

    headers = {
        "Content-Type": "application/octet-stream"
    }

    try:
        with open(cert_file_path, 'rb') as file:
            cert_data = file.read()

        response = requests.post(
            url,
            data=cert_data,
            headers=headers,
            auth=HTTPDigestAuth(username, password),
            verify=cert_path if https and cert_path else https,
            timeout=15
        )

        print(f"Status code: {response.status_code}")
        print(f"Resposta: {response.text}")
        return response.status_code == 200

    except Exception as e:
        print(f"Erro ao enviar certificado: {e}")
        return False

def upload_pfx_certificate_pkcs12(camera_ip, username, password, cert_file_path, custom_id, pfx_password, https=False, cert_path=None):
    """
    Envia um certificado em formato .pfx (PKCS#12) com XML e conteúdo binário no mesmo corpo.

    Args:
        cert_file_path: Caminho do .pfx contendo certificado e chave.
        custom_id: Identificador do certificado na câmera.
        pfx_password: Senha usada ao gerar o .pfx.
        https: Se True, usa HTTPS.
        cert_path: Caminho para CA confiável (se https for True).

    Returns:
        True se sucesso, False caso contrário.
    """
    protocol = "https" if https else "http"
    url = f"{protocol}://{camera_ip}/ISAPI/Security/serverCertificate/certificate?customID={custom_id}"

    # Codifica a senha do .pfx em base64
    encoded_password = base64.b64encode(pfx_password.encode('utf-8')).decode('utf-8')

    print(f"\nencoded_password: {encoded_password}\n")

    # Monta o cabeçalho XML que deve vir antes do conteúdo binário
    xml_header = f"""<?xml version="1.0" encoding="UTF-8"?>
    <CertificateReq version="1.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
        <certificateMode>signingRequest</certificateMode>
        <privateKeyMode>seperateKey</privateKeyMode>
        <seperateKeyPassword></seperateKeyPassword>
        <PKCSPassword></PKCSPassword>
        <dataType>certificate</dataType>
    </CertificateReq>"""

    try:
        with open(cert_file_path, 'rb') as file:
            cert_bin = file.read()

        # Junta XML + binário como corpo único
        full_payload = xml_header.encode('utf-8') + cert_bin

        headers = {
            "Content-Type": "application/xml"
        }

        response = requests.post(
            url,
            data=full_payload,
            headers=headers,
            auth=HTTPDigestAuth(username, password),
            verify=cert_path if https and cert_path else https,
            timeout=20
        )

        print(f"Status code: {response.status_code}")
        print(f"Resposta: {response.text}")
        return response.status_code == 200

    except Exception as e:
        print(f"Erro ao enviar certificado: {e}")
        return False

camera_ip   = "" 
username    = ""
password    = ""

#shutter_levels = get_shutter_time_levels_from_file(camera_ip, username, password)
#if shutter_levels:
    #print("Lista de níveis de obturador disponíveis:", shutter_levels)

#get_exposure_mode(camera_ip, username, password, channel_id=1, parameter_type="exposureMode")
#get_shutter_options(camera_ip, username, password, channel_id=1)
#set_shutter(camera_ip, username, password, shutter_level="1/120")
#set_ircut(camera_ip, username, password, ircut_filter_type="day");
#set_gain_level(camera_ip, username, password, channel_id=1, gain_level=40)
#get_parametros_imagem(camera_ip, username, password)
#set_white_balance(camera_ip, username, password, channel_id=1, white_balance_style="daylightLamp") 
#set_white_balance(camera_ip, username, password, channel_id=1, white_balance_style="manual", white_balance_red=60, white_balance_blue=70)
#get_device_status_capacities(camera_ip, username, password, "7a26_get_device_status_capacities")
#get_parametros_imagem(camera_ip, username, password, "7a26_get_parametros_imagem")
#get_system_capacities(camera_ip, username, password, "7a26_get_system_capacities") #é os isSuported
#get_image_capabilities(camera_ip, username, password, "1027_get_image_capacities") 
#set_distorcao_lente(camera_ip, username, password, enabled=False) #OK
#set_eis(camera_ip, username, password, enabled=True)
#set_exposure_by_modes(camera_ip, username, password, modo="manual") #modo manual
#set_exposure_by_modes(camera_ip, username, pa#OKssword, modo="p-iris-auto") #p-iris-auto
#set_exposure_by_modes(camera_ip, username, password, modo="p-iris-manual", iris_level=20) #p-iris-manual
#get_image_capabilities(camera_ip, username, password, "1027_get_image_capacities") 
#status = get_color_config(camera_ip, username, password, https=True, cert_path="/etc/ssl/hikvision_with_san.pem") #OK teste com certificado

########## NEW SECURITY FUNCTIONS OK #################

#get_security_capabilities(camera_ip, username, password, https=False)              #OK
#get_certificate_select_capabilities(camera_ip, username, password, https=False)    #OK ruim sem muita informacao
#get_server_certificates(camera_ip, username, password, https=False)                #OK As infors do propriedades do certificado
#delete_server_certificate(camera_ip, username, password, custom_id="cul", https=False) #OK apaga com o CustomID que dá pra ver pelo get_server_certificates
#get_device_certificate_capabilities(camera_ip, username, password, https=False, cert_path=None) #OK Pega só os campos que existem como status id os opt
########## THIS DONT WORK (yet) ###############

status = upload_pfx_certificate_pkcs12(
    camera_ip,
    username,
    password,
    cert_file_path="",
    custom_id="",
    pfx_password="",  # senha usada na geração do .pfx
    https=True,
    cert_path=""
)
print (status)

