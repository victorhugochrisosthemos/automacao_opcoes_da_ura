import socket
import time
import threading
from enum import Enum
import re
import random
import struct

class URAState(Enum):
    INIT = 0
    MAIN_MENU = 1
    SUB_MENU = 2
    TRANSFERRING = 3
    WAITING_FOR_ANSWER = 4
    SENDING_OPTION = 5
    OPTION_SENT = 6
    PLAYING_MESSAGE = 7
    ACTIVE_CALL = 8

class SIPURAServer:
    def __init__(self, host='0.0.0.0', port=5061, pbx_ip='10.1.43.55', pbx_port=5090, rtp_port=13010):
        self.host = host
        self.port = port
        self.pbx_ip = pbx_ip
        self.pbx_port = pbx_port
        self.rtp_port = rtp_port
        self.running = False
        self.ura_state = URAState.INIT
        self.current_call_id = None
        self.current_from = None
        self.current_to = None
        self.current_via = None
        self.current_cseq = 1
        self.remote_contact = None
        self.registered_clients = {}
        self.transfer_target = None
        self.selected_option = None
        self.selected_menu_value = None
        self.call_start_time = None
        self.message_to_play = None
        self.rtp_socket = None
        self.rtp_active = False
        self.tag_counter = random.randint(13010, 99999)
        
        # Variáveis para controle de áudio
        self.softphone_rtp_ip = None
        self.softphone_rtp_port = None
        self.pbx_rtp_ip = None
        self.pbx_rtp_port = None
        
        # Configuração da árvore de menus
        self.menu_tree = {
            'main': {
                '1': {'description': 'Suporte Técnico', 'action': 'submenu', 'target': 'suporte', 'menu': '1'},
                '2': {'description': 'Financeiro', 'action': 'submenu', 'target': 'financeiro', 'menu': '2'},
                '3': {'description': 'Vendas', 'action': 'submenu', 'target': 'vendas', 'menu': '3'},
                '4': {'description': 'Atendimento ao Cliente', 'action': 'submenu', 'target': 'sac', 'menu': '4'},
                '0': {'description': 'Operador', 'action': 'transfer', 'target': '1000'}
            },
            'suporte': {
                '1': {'description': 'Hardware', 'action': 'transfer', 'target': '2001', 'menu': '1'},
                '2': {'description': 'Software', 'action': 'transfer', 'target': '2002', 'menu': '2'},
                '3': {'description': 'Redes', 'action': 'transfer', 'target': '2003', 'menu': '3'},
                '0': {'description': 'Voltar', 'action': 'back'}
            },
            'financeiro': {
                '1': {'description': 'Cobrança', 'action': 'transfer', 'target': '3001', 'menu': '1'},
                '2': {'description': 'Pagamentos', 'action': 'transfer', 'target': '3002', 'menu': '2'},
                '0': {'description': 'Voltar', 'action': 'back'}
            },
            'vendas': {
                '1': {'description': 'Produtos', 'action': 'transfer', 'target': '4001', 'menu': '1'},
                '2': {'description': 'Orçamentos', 'action': 'transfer', 'target': '4002', 'menu': '2'},
                '0': {'description': 'Voltar', 'action': 'back'}
            },
            'sac': {
                '1': {'description': 'Reclamações', 'action': 'transfer', 'target': '5001', 'menu': '1'},
                '2': {'description': 'Sugestões', 'action': 'transfer', 'target': '5002', 'menu': '2'},
                '0': {'description': 'Voltar', 'action': 'back'}
            }
        }
        
        self.current_menu = 'main'
        self.menu_history = []
        self.setup_rtp_socket()

    def setup_rtp_socket(self):
        """Configura o socket RTP para transmissão de áudio"""
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtp_socket.bind((self.host, self.rtp_port))
        print(f"Socket RTP configurado em {self.host}:{self.rtp_port}")

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        print(f"Servidor SIP URA rodando em {self.host}:{self.port}")
        
        # Thread para console
        console_thread = threading.Thread(target=self.handle_console_input)
        console_thread.daemon = True
        console_thread.start()
        
        # Thread para receber RTP
        rtp_receive_thread = threading.Thread(target=self.receive_rtp)
        rtp_receive_thread.daemon = True
        rtp_receive_thread.start()
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(10240)
                message = data.decode('utf-8')
                print(f"\nMensagem recebida de {addr}:\n{message}")
                
                self.process_sip_message(message, addr)
            except Exception as e:
                print(f"Erro ao processar mensagem: {e}")
                
    def receive_rtp(self):
        """Thread para receber pacotes RTP e encaminhar"""
        while self.running:
            try:
                data, addr = self.rtp_socket.recvfrom(2048)
                
                # Verifica se é um pacote RTP válido (pelo menos 12 bytes de header)
                if len(data) >= 12:
                    # Determina de onde veio o pacote e para onde encaminhar
                    if addr[0] == self.softphone_rtp_ip and addr[1] == self.softphone_rtp_port:
                        # Pacote veio do softphone - encaminha para PBX
                        if self.pbx_rtp_ip and self.pbx_rtp_port:
                            self.rtp_socket.sendto(data, (self.pbx_rtp_ip, self.pbx_rtp_port))
                    elif addr[0] == self.pbx_rtp_ip and addr[1] == self.pbx_rtp_port:
                        # Pacote veio da PBX - encaminha para softphone
                        if self.softphone_rtp_ip and self.softphone_rtp_port:
                            self.rtp_socket.sendto(data, (self.softphone_rtp_ip, self.softphone_rtp_port))
                
            except Exception as e:
                print(f"Erro ao receber RTP: {e}")
                time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
        if self.rtp_socket:
            self.rtp_socket.close()
        print("Servidor e sockets encerrados.")
        
    def process_sip_message(self, message, addr):
        if "REGISTER" in message:
            self.handle_register(message, addr)
        elif "INVITE" in message and "INVITE" in self.get_header(message, "CSeq"):
            self.handle_invite(message, addr)
        elif "ACK" in message and "ACK" in self.get_header(message, "CSeq"):
            self.handle_ack(message, addr)
        elif "BYE" in message:
            self.handle_bye(message, addr)
        elif "CANCEL" in message:
            self.handle_cancel(message, addr)
        elif "REFER" in message:
            self.handle_refer(message, addr)
        elif "OPTIONS" in message:
            self.handle_options(message, addr)
        elif "SIP/2.0 100 Trying" in message:
            self.handle_trying(message, addr)
        elif "SIP/2.0 180 Ringing" in message:
            self.handle_ringing(message, addr)
        elif "SIP/2.0 200 OK" in message:
            if self.ura_state == URAState.TRANSFERRING:
                self.handle_transfer_ok(message, addr)
            elif self.ura_state == URAState.WAITING_FOR_ANSWER:
                self.handle_pbx_answer(message, addr)
            elif self.ura_state == URAState.SENDING_OPTION:
                self.handle_option_sent(message, addr)
            else:
                self.handle_generic_ok(message, addr)
        elif "SIP/2.0 401 Unauthorized" in message:
            self.handle_unauthorized(message, addr)
        elif "SIP/2.0 407 Proxy Authentication Required" in message:
            self.handle_proxy_auth(message, addr)
            
    def generate_tag(self):
        self.tag_counter += 1
        return f"{int(time.time())}{self.tag_counter}"
            
    def handle_register(self, message, addr):
        from_match = re.search(r'From:\s*<sip:([^@]+)', message)
        if from_match:
            user = from_match.group(1)
            self.registered_clients[user] = addr
            print(f"Cliente registrado: {user} de {addr}")
            
            response = (
                "SIP/2.0 200 OK\r\n"
                f"Via: {self.get_header(message, 'Via')}\r\n"
                f"From: {self.get_header(message, 'From')}\r\n"
                f"To: {self.get_header(message, 'To')};tag={self.generate_tag()}\r\n"
                f"Call-ID: {self.get_header(message, 'Call-ID')}\r\n"
                f"CSeq: {self.get_header(message, 'CSeq')}\r\n"
                "Contact: <sip:ura@{}:{}>\r\n"
                "Content-Length: 0\r\n\r\n"
            ).format(self.host, self.port)
            
            self.sock.sendto(response.encode('utf-8'), addr)
            
    def handle_invite(self, message, addr):
        call_id = self.get_header(message, 'Call-ID')
        self.current_call_id = call_id
        self.current_from = self.get_header(message, 'From')
        self.current_to = self.get_header(message, 'To')
        self.current_via = self.get_header(message, 'Via')
        self.current_cseq = int(self.get_header(message, 'CSeq').split()[0])
        self.call_start_time = time.time()
        
        # Extrai o Contact do remetente
        contact = self.get_header(message, 'Contact')
        if contact:
            self.remote_contact = self.parse_contact(contact)
        
        # Extrai informações SDP para RTP do softphone
        sdp_match = re.search(r'c=IN IP4 (\d+\.\d+\.\d+\.\d+)', message)
        if sdp_match:
            self.softphone_rtp_ip = sdp_match.group(1)
            m_match = re.search(r'm=audio (\d+)', message)
            if m_match:
                self.softphone_rtp_port = int(m_match.group(1))
                print(f"RTP do softphone configurado: {self.softphone_rtp_ip}:{self.softphone_rtp_port}")
        
        trying_response = (
            "SIP/2.0 100 Trying\r\n"
            f"Via: {self.current_via}\r\n"
            f"From: {self.current_from}\r\n"
            f"To: {self.current_to}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {self.current_cseq} INVITE\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        self.sock.sendto(trying_response.encode('utf-8'), addr)
        
        ringing_response = (
            "SIP/2.0 180 Ringing\r\n"
            f"Via: {self.current_via}\r\n"
            f"From: {self.current_from}\r\n"
            f"To: {self.current_to};tag={self.generate_tag()}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {self.current_cseq} INVITE\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        self.sock.sendto(ringing_response.encode('utf-8'), addr)
        
        # Prepara SDP com nossa porta RTP
        sdp_body = (
            "v=0\r\n"
            "o=- 123456789 123456789 IN IP4 {}\r\n"
            "s=URA SIP\r\n"
            "c=IN IP4 {}\r\n"
            "t=0 0\r\n"
            "m=audio {} RTP/AVP 0 8 101\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
            "a=rtpmap:8 PCMA/8000\r\n"
            "a=rtpmap:101 telephone-event/8000\r\n"
            "a=fmtp:101 0-16\r\n"
        ).format(self.host, self.host, self.rtp_port)
        
        ok_response = (
            "SIP/2.0 200 OK\r\n"
            f"Via: {self.current_via}\r\n"
            f"From: {self.current_from}\r\n"
            f"To: {self.current_to};tag={self.generate_tag()}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {self.current_cseq} INVITE\r\n"
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {len(sdp_body)}\r\n\r\n"
            f"{sdp_body}"
        )
        self.sock.sendto(ok_response.encode('utf-8'), addr)
        
        self.ura_state = URAState.MAIN_MENU
        self.current_menu = 'main'
        self.menu_history = []
        
        print("Chamada atendida. Aguardando seleção de menu.")
        
    def handle_ack(self, message, addr):
        print("ACK recebido. Conexão estabelecida.")
        self.ura_state = URAState.ACTIVE_CALL
        
        # Verifica se o ACK contém SDP para atualizar os parâmetros RTP
        if "application/sdp" in message:
            sdp_match = re.search(r'c=IN IP4 (\d+\.\d+\.\d+\.\d+)', message)
            if sdp_match:
                self.softphone_rtp_ip = sdp_match.group(1)
                m_match = re.search(r'm=audio (\d+)', message)
                if m_match:
                    self.softphone_rtp_port = int(m_match.group(1))
                    print(f"RTP do softphone atualizado: {self.softphone_rtp_ip}:{self.softphone_rtp_port}")
        
    def handle_bye(self, message, addr):
        call_id = self.get_header(message, 'Call-ID')
        
        response = (
            "SIP/2.0 200 OK\r\n"
            f"Via: {self.get_header(message, 'Via')}\r\n"
            f"From: {self.get_header(message, 'From')}\r\n"
            f"To: {self.get_header(message, 'To')};tag={self.generate_tag()}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {self.get_header(message, 'CSeq')}\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        self.sock.sendto(response.encode('utf-8'), addr)
        
        self.cleanup_call()
        print("Chamada encerrada.")
        
    def cleanup_call(self):
        """Limpa todos os dados da chamada atual"""
        self.ura_state = URAState.INIT
        self.current_call_id = None
        self.current_menu = 'main'
        self.menu_history = []
        self.transfer_target = None
        self.selected_option = None
        self.selected_menu_value = None
        self.remote_contact = None
        self.softphone_rtp_ip = None
        self.softphone_rtp_port = None
        self.pbx_rtp_ip = None
        self.pbx_rtp_port = None
        
    def handle_cancel(self, message, addr):
        call_id = self.get_header(message, 'Call-ID')
        
        response = (
            "SIP/2.0 200 OK\r\n"
            f"Via: {self.get_header(message, 'Via')}\r\n"
            f"From: {self.get_header(message, 'From')}\r\n"
            f"To: {self.get_header(message, 'To')};tag={self.generate_tag()}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {self.get_header(message, 'CSeq')}\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        self.sock.sendto(response.encode('utf-8'), addr)
        
        self.cleanup_call()
        print("Chamada cancelada.")
        
    def handle_refer(self, message, addr):
        print("Mensagem REFER recebida, tratando...")
        call_id = self.get_header(message, 'Call-ID')
        
        response = (
            "SIP/2.0 202 Accepted\r\n"
            f"Via: {self.get_header(message, 'Via')}\r\n"
            f"From: {self.get_header(message, 'From')}\r\n"
            f"To: {self.get_header(message, 'To')};tag={self.generate_tag()}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {self.get_header(message, 'CSeq')}\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        self.sock.sendto(response.encode('utf-8'), addr)
        
    def handle_options(self, message, addr):
        print("Mensagem OPTIONS recebida, respondendo...")
        call_id = self.get_header(message, 'Call-ID')
        
        response = (
            "SIP/2.0 200 OK\r\n"
            f"Via: {self.get_header(message, 'Via')}\r\n"
            f"From: {self.get_header(message, 'From')}\r\n"
            f"To: {self.get_header(message, 'To')};tag={self.generate_tag()}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {self.get_header(message, 'CSeq')}\r\n"
            "Allow: INVITE, ACK, BYE, CANCEL, OPTIONS, REFER\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        self.sock.sendto(response.encode('utf-8'), addr)
        
    def handle_trying(self, message, addr):
        """Lida com mensagem 100 Trying da PBX"""
        print("PBX está processando a chamada (100 Trying)")
        
        # Não precisamos responder ao 100 Trying, é apenas informativo
        
    def handle_ringing(self, message, addr):
        """Lida com mensagem 180 Ringing da PBX"""
        print("PBX informa que a chamada está tocando (180 Ringing)")
        
        # Encaminha o 180 Ringing para o softphone
        if self.remote_contact:
            via_header = self.get_header(message, 'Via')
            from_header = self.get_header(message, 'From')
            to_header = self.get_header(message, 'To')
            call_id = self.get_header(message, 'Call-ID')
            cseq = self.get_header(message, 'CSeq')
            
            ringing_response = (
                "SIP/2.0 180 Ringing\r\n"
                f"Via: {via_header}\r\n"
                f"From: {from_header}\r\n"
                f"To: {to_header}\r\n"
                f"Call-ID: {call_id}\r\n"
                f"CSeq: {cseq}\r\n"
                "Content-Length: 0\r\n\r\n"
            )
            self.sock.sendto(ringing_response.encode('utf-8'), self.remote_contact)
        
    def handle_pbx_answer(self, message, addr):
        """Lidar com o 200 OK recebido da PBX após transferência"""
        print("\n=== 200 OK recebido da PBX ===")
        
        # Extrai informações SDP da PBX
        sdp_match = re.search(r'c=IN IP4 (\d+\.\d+\.\d+\.\d+)', message)
        if sdp_match:
            self.pbx_rtp_ip = sdp_match.group(1)
            m_match = re.search(r'm=audio (\d+)', message)
            if m_match:
                self.pbx_rtp_port = int(m_match.group(1))
                print(f"RTP da PBX configurado: {self.pbx_rtp_ip}:{self.pbx_rtp_port}")
        
        # Extrai headers importantes
        via_header = self.get_header(message, 'Via')
        from_header = self.get_header(message, 'From')
        to_header = self.get_header(message, 'To')
        call_id = self.get_header(message, 'Call-ID')
        cseq = self.get_header(message, 'CSeq')
        
        # Extrai o branch do Via header
        branch_match = re.search(r'branch=([^;]+)', via_header)
        branch = branch_match.group(1) if branch_match else f"z9hG4bK{int(time.time())}"
        
        # Envia ACK para confirmar o 200 OK para a PBX
        ack_msg = (
            f"ACK sip:{self.transfer_target}@{self.pbx_ip}:{self.pbx_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.host}:{self.port};branch={branch}\r\n"
            f"From: {from_header}\r\n"
            f"To: {to_header}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {cseq.split()[0]} ACK\r\n"
            f"Contact: <sip:ura@{self.host}:{self.port}>\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        
        print("\nEnviando ACK para PBX:")
        print(ack_msg)
        self.sock.sendto(ack_msg.encode('utf-8'), (self.pbx_ip, self.pbx_port))
        
        # Envia 200 OK para o softphone
        if self.remote_contact:
            # Prepara SDP com nossa porta RTP
            sdp_body = (
                "v=0\r\n"
                "o=- 123456789 123456789 IN IP4 {}\r\n"
                "s=URA SIP\r\n"
                "c=IN IP4 {}\r\n"
                "t=0 0\r\n"
                "m=audio {} RTP/AVP 0 8 101\r\n"
                "a=rtpmap:0 PCMU/8000\r\n"
                "a=rtpmap:8 PCMA/8000\r\n"
                "a=rtpmap:101 telephone-event/8000\r\n"
                "a=fmtp:101 0-16\r\n"
            ).format(self.host, self.host, self.rtp_port)
            
            ok_response = (
                "SIP/2.0 200 OK\r\n"
                f"Via: {self.current_via}\r\n"
                f"From: {self.current_from}\r\n"
                f"To: {self.current_to};tag={self.generate_tag()}\r\n"
                f"Call-ID: {self.current_call_id}\r\n"
                f"CSeq: {self.current_cseq} INVITE\r\n"
                "Content-Type: application/sdp\r\n"
                f"Content-Length: {len(sdp_body)}\r\n\r\n"
                f"{sdp_body}"
            )
            
            print("\nEnviando 200 OK para softphone:")
            print(ok_response)
            self.sock.sendto(ok_response.encode('utf-8'), self.remote_contact)
        
        if self.selected_menu_value:
            print(f"\nPreparando para enviar opção {self.selected_menu_value} após 1 segundo...")
            time.sleep(1)
            
            # Prepara o novo INVITE com a opção
            sdp_body = (
                "v=0\r\n"
                "o=- 123456789 123456789 IN IP4 {}\r\n"
                "s=URA SIP\r\n"
                "c=IN IP4 {}\r\n"
                "t=0 0\r\n"
                "m=audio {} RTP/AVP 0 8 101\r\n"
                "a=rtpmap:0 PCMU/8000\r\n"
                "a=rtpmap:8 PCMA/8000\r\n"
                "a=rtpmap:101 telephone-event/8000\r\n"
                "a=fmtp:101 0-16\r\n"
            ).format(self.host, self.host, self.rtp_port)

            invite_msg = (
                f"INVITE sip:{self.selected_menu_value}@{self.pbx_ip}:{self.pbx_port} SIP/2.0\r\n"
                f"Via: SIP/2.0/UDP {self.host}:{self.port};branch=z9hG4bK{int(time.time())}\r\n"
                f"From: {self.current_from}\r\n"
                f"To: <sip:{self.selected_menu_value}@{self.pbx_ip}:{self.pbx_port}>\r\n"
                f"Call-ID: {self.current_call_id}\r\n"
                f"CSeq: {self.current_cseq + 2} INVITE\r\n"
                f"Contact: <sip:ura@{self.host}:{self.port}>\r\n"
                "Content-Type: application/sdp\r\n"
                f"Content-Length: {len(sdp_body)}\r\n\r\n"
                f"{sdp_body}"
            )
            
            print("\nEnviando novo INVITE com a opção selecionada:")
            print(invite_msg)
            self.sock.sendto(invite_msg.encode('utf-8'), (self.pbx_ip, self.pbx_port))
            
            self.ura_state = URAState.SENDING_OPTION
        else:
            print("\nNenhuma opção para enviar. Chamada transferida normalmente.")
            self.ura_state = URAState.OPTION_SENT
        
    def handle_transfer_ok(self, message, addr):
        print("\nTransferência confirmada (200 OK recebido). Aguardando resposta da central...")
        self.ura_state = URAState.WAITING_FOR_ANSWER
        
    def handle_option_sent(self, message, addr):
        print("\nOpção enviada com sucesso (200 OK recebido). Encerrando processo.")
        
        to_header = self.get_header(message, 'To')
        ack_msg = (
            f"ACK sip:{self.selected_menu_value}@{self.pbx_ip}:{self.pbx_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.host}:{self.port};branch=z9hG4bK{int(time.time())}\r\n"
            f"From: {self.current_from}\r\n"
            f"To: {to_header}\r\n"
            f"Call-ID: {self.current_call_id}\r\n"
            f"CSeq: {self.current_cseq + 2} ACK\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        
        print("\nEnviando ACK para confirmar opção enviada:")
        print(ack_msg)
        self.sock.sendto(ack_msg.encode('utf-8'), (self.pbx_ip, self.pbx_port))
        
        self.cleanup_call()
        
    def handle_generic_ok(self, message, addr):
        print("200 OK genérico recebido")
        call_id = self.get_header(message, 'Call-ID')
        cseq = self.get_header(message, 'CSeq')
        
        if "INVITE" in cseq:
            # Responde com ACK
            ack_msg = (
                f"ACK sip:{self.get_header(message, 'To').split(';')[0].strip('<>')} SIP/2.0\r\n"
                f"Via: SIP/2.0/UDP {self.host}:{self.port};branch=z9hG4bK{int(time.time())}\r\n"
                f"From: {self.get_header(message, 'From')}\r\n"
                f"To: {self.get_header(message, 'To')}\r\n"
                f"Call-ID: {call_id}\r\n"
                f"CSeq: {int(cseq.split()[0])} ACK\r\n"
                "Content-Length: 0\r\n\r\n"
            )
            self.sock.sendto(ack_msg.encode('utf-8'), addr)
            
    def handle_unauthorized(self, message, addr):
        print("Erro 401 Unauthorized recebido")
        
    def handle_proxy_auth(self, message, addr):
        print("Erro 407 Proxy Authentication Required recebido")
        
    def get_header(self, message, header_name):
        pattern = re.compile(rf"{header_name}:\s*(.*?)\r\n", re.IGNORECASE)
        match = pattern.search(message)
        return match.group(1) if match else ""
        
    def parse_contact(self, contact_header):
        """Extrai IP e porta do cabeçalho Contact"""
        match = re.search(r'sip:[^@]+@([\d.]+)(?::(\d+))?', contact_header)
        if match:
            ip = match.group(1)
            port = int(match.group(2)) if match.group(2) else 5060
            return (ip, port)
        return None
        
    def handle_console_input(self):
        while self.running:
            try:
                if self.ura_state in [URAState.MAIN_MENU, URAState.SUB_MENU, URAState.ACTIVE_CALL]:
                    self.print_current_menu()
                    
                    option = input("Digite a opção desejada, 'd' para digitar ramal diretamente ou 'q' para sair: ").strip()
                    
                    if option.lower() == 'q':
                        self.stop()
                        break
                    elif option.lower() == 'd' and self.ura_state != URAState.ACTIVE_CALL:
                        target = input("Digite o número do ramal para transferência direta: ").strip()
                        if target.isdigit():
                            print(f"Transferindo diretamente para ramal {target}...")
                            self.transfer_call(target)
                        else:
                            print("Número inválido. Digite apenas dígitos.")
                    elif self.ura_state == URAState.ACTIVE_CALL:
                        print("Chamada ativa. Use 'h' para ajuda.")
                        if option.lower() == 'h':
                            print("Comandos disponíveis:")
                            print("b - Enviar sinal de busy (486 Busy Here)")
                            print("e - Encerrar chamada (BYE)")
                        elif option.lower() == 'b':
                            self.send_busy()
                        elif option.lower() == 'e':
                            self.send_bye()
                    else:
                        self.process_menu_option(option)
                    
            except Exception as e:
                print(f"Erro no console: {e}")
                
    def send_busy(self):
        if not self.current_call_id:
            print("Nenhuma chamada ativa")
            return
            
        response = (
            "SIP/2.0 486 Busy Here\r\n"
            f"Via: {self.current_via}\r\n"
            f"From: {self.current_from}\r\n"
            f"To: {self.current_to};tag={self.generate_tag()}\r\n"
            f"Call-ID: {self.current_call_id}\r\n"
            f"CSeq: {self.current_cseq} INVITE\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        
        self.sock.sendto(response.encode('utf-8'), self.remote_contact or (self.pbx_ip, self.pbx_port))
        self.cleanup_call()
        print("Sinal de ocupado enviado.")
        
    def send_bye(self):
        if not self.current_call_id:
            print("Nenhuma chamada ativa")
            return
            
        bye_msg = (
            f"BYE sip:{self.remote_contact[0]}:{self.remote_contact[1]} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.host}:{self.port};branch=z9hG4bK{int(time.time())}\r\n"
            f"From: {self.current_from}\r\n"
            f"To: {self.current_to}\r\n"
            f"Call-ID: {self.current_call_id}\r\n"
            f"CSeq: {self.current_cseq + 1} BYE\r\n"
            "Content-Length: 0\r\n\r\n"
        )
        
        self.sock.sendto(bye_msg.encode('utf-8'), self.remote_contact or (self.pbx_ip, self.pbx_port))
        self.cleanup_call()
        print("Chamada encerrada com BYE.")
                
    def print_current_menu(self):
        print("\n" + "="*40)
        if self.ura_state == URAState.ACTIVE_CALL:
            print("Chamada Ativa - Menu de Controle")
            print("="*40)
            print("b - Enviar sinal de ocupado")
            print("e - Encerrar chamada")
            print("="*40)
            return
            
        print(f"Menu {'Principal' if self.current_menu == 'main' else self.current_menu}")
        print("="*40)
        
        menu = self.menu_tree[self.current_menu]
        for key, item in menu.items():
            print(f"{key} - {item['description']}")
            
        print("d - Transferência direta (digitar ramal)")
        print("="*40)
                
    def process_menu_option(self, option):
        if option not in self.menu_tree[self.current_menu]:
            print("Opção inválida. Tente novamente.")
            return
            
        menu_item = self.menu_tree[self.current_menu][option]
        
        if menu_item['action'] == 'submenu':
            self.menu_history.append(self.current_menu)
            self.current_menu = menu_item['target']
            self.ura_state = URAState.SUB_MENU
            print(f"Indo para submenu: {menu_item['target']}")
            
        elif menu_item['action'] == 'back':
            if self.menu_history:
                self.current_menu = self.menu_history.pop()
                if not self.menu_history:
                    self.ura_state = URAState.MAIN_MENU
                print(f"Voltando para menu: {self.current_menu}")
            else:
                print("Já está no menu principal.")
                
        elif menu_item['action'] == 'transfer':
            target = menu_item['target']
            self.selected_option = option
            self.selected_menu_value = menu_item.get('menu', None)
            
            print(f"Transferindo para ramal {target}...")
            if self.selected_menu_value:
                print(f"Após atendimento, será enviada a opção: {self.selected_menu_value}")
            self.transfer_call(target)
            
    def transfer_call(self, target):
        if not self.current_call_id:
            print("Nenhuma chamada ativa para transferir")
            return

        self.transfer_target = target
        
        sdp_body = (
            "v=0\r\n"
            "o=- 123456789 123456789 IN IP4 {}\r\n"
            "s=URA SIP\r\n"
            "c=IN IP4 {}\r\n"
            "t=0 0\r\n"
            "m=audio {} RTP/AVP 0 8 101\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
            "a=rtpmap:8 PCMA/8000\r\n"
            "a=rtpmap:101 telephone-event/8000\r\n"
            "a=fmtp:101 0-16\r\n"
        ).format(self.host, self.host, self.rtp_port)

        invite_msg = (
            f"INVITE sip:{target}@{self.pbx_ip}:{self.pbx_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.host}:{self.port};branch=z9hG4bK{int(time.time())}\r\n"
            f"From: {self.current_from}\r\n"
            f"To: <sip:{target}@{self.pbx_ip}:{self.pbx_port}>\r\n"
            f"Call-ID: {self.current_call_id}\r\n"
            f"CSeq: {self.current_cseq + 1} INVITE\r\n"
            f"Contact: <sip:ura@{self.host}:{self.port}>\r\n"
            "Content-Type: application/sdp\r\n"
            f"Content-Length: {len(sdp_body)}\r\n\r\n"
            f"{sdp_body}"
        )

        print(f"\nEnviando INVITE para transferência para {self.pbx_ip}:{self.pbx_port}")
        print(invite_msg)
        self.sock.sendto(invite_msg.encode('utf-8'), (self.pbx_ip, self.pbx_port))
        
        self.ura_state = URAState.TRANSFERRING
        print(f"Transferência para ramal {target} enviada ao PABX via INVITE")

if __name__ == "__main__":
    server = SIPURAServer(host='192.168.15.7', port=5091, pbx_ip='10.1.43.55', pbx_port=5090, rtp_port=13010)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("Servidor encerrado.")