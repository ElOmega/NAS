import json
import os
import shutil
#import telnetlib
import time

#def send_config_to_router(host, port, config_file):
#    tn = telnetlib.Telnet(host, port)    
#    tn.read_until(b">")
#    tn.write(b"enable\n")
#   tn.read_until(b"#")
#    tn.write(b"terminal length 0\n")
#   tn.write(b"conf t\n")
#
 #   with open(config_file, 'r') as file:
  #      for line in file:
   #         tn.write(line.strip().encode('ascii') + b"\n")
    #        time.sleep(0.1)  # laisse le temps au routeur d'encaisser

    #tn.write(b"end\n")
    #tn.write(b"write memory\n")
    #tn.write(b"exit\n")

    #print(tn.read_all().decode('ascii'))

# Exemple d’appel
#send_config_to_router("127.0.0.1", 5000, "i1_startup-config.cfg")


nombre_router_AS=0

def ipv4(adresse_ip,number):
    adresse_ip = adresse_ip.split('/')
    adresse_ip = adresse_ip[0]
    adresse_ip = adresse_ip +"."+ number
    return adresse_ip

def loopback(loopback_addr,number):
    loopback_addr = loopback_addr[0].split('/')
    loopback_addr = loopback_addr[0]+"."+str(number)
    return loopback_addr


def read_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {file_path}.")
        return None

def create_cfg_config(base_server_config, router, intent, AS,liste_extreme_AS_mid):
    global nombre_router_AS

    fichier = f'i{router[1:]}_startup-config.cfg'
    with open(f'i{router[1:]}_startup-config.cfg', 'w') as file:
        number=router[1:]
        for sentence in base_server_config:
            file.write(sentence + '\n!\n')
            if sentence == "boot-end-marker" and 'externe' in intent[AS]['router'][router] and AS == "AS_mid":
                liste_router_voisin = list(intent[AS]['router'][router]['externe'])
                for i in range(1,len(liste_router_voisin)+1):
                    file.write(f"vrf definition Client_{i}\n")
                    file.write(f" rd 100:{i}\n")
                    file.write(f" route-target import 100:{i}000\n")
                    file.write(f" route-target export 100:{i}000\n") 
                    file.write(f" !\n")                           
                    file.write(f" address-family ipv4\n")
                    file.write(f" exit-address-family\n")
                    file.write("!\n")

            elif sentence == "service timestamps log datetime msec":
                file.write(f"hostname {router}\n")
            elif sentence == "ip tcp synwait-time 5":
                #mise en place de l'interface loopback
                if "address_loopback" in intent[AS]:

                    file.write(f"interface Loopback0\n ip address {loopback(intent[AS]['address_loopback'],number)} 255.255.255.255\n")
                    if (AS == "AS_mid") :
                        file.write(" ip ospf 1 area 0\n")
                    file.write("!\n")
                #IPV4
                for position in intent[AS]['router'][router]:
                    if position == "ebgp_neighbors":
                        continue

                    elif position == "interne":
                        for router_other in intent[AS]['router'][router][position]: 
                            file.write(f"interface {intent[AS]['router'][router][position][router_other]}\n" 
                               f" ip address {ipv4(intent[AS]['address'][0],str(nombre_router_AS))} 255.255.255.252\n")
                            file.write(" ip ospf 1 area 0\n")
                            file.write(" negotiation auto\n mpls ip\n")
                            file.write("!\n")
                            if (nombre_router_AS%4 == 1) : 
                                nombre_router_AS+=1
                            else : 
                                nombre_router_AS+=3
                    elif position == "externe":
                        nbclient=1
                        for other_AS in intent:
                            if other_AS == AS:
                                continue
                            for router_other in intent[other_AS]['router']:
                                if router_other == router or router not in intent[other_AS]['router'][router_other].get('externe', {}) :
                                    continue
                                file.write(f"interface {intent[AS]['router'][router]['externe'][router_other]}\n")
                                if (AS == "AS_mid") : 
                                    file.write(f" vrf forwarding Client_{nbclient}\n")
                                    nbclient += 1
                                    file.write(f" ip address {ipv4(intent[other_AS]['address'][0],str(1))} 255.255.255.252\n")
                                    file.write(f"!\n")
                                else : 
                                    file.write(f" ip address {ipv4(intent[AS]['address'][0],str(2))} 255.255.255.252\n")
                                    file.write(f"!\n")

                                

                    
                    else : 

                        for router_other in intent[AS]['router'][router]: 
                            file.write(f"interface {intent[AS]['router'][router][router_other]}\n" 
                               f" ip address {ipv4(intent[AS]['address'][0],str(2))} 255.255.255.252\n")
                            if (AS == "AS_mid") : 
                                file.write(" ip ospf 1 area 0\n")
                                file.write(" negotiation auto\n mpls ip\n")
                            file.write("!\n")

                #CONFIGURATION OSPF
                if (AS == "AS_mid"):
                    file.write("router ospf 1\n")
                    file.write(f" router-id {str(number)+'.'+str(number)+'.'+str(number)+'.'+str(number)}\n")
                    file.write(" mpls ldp autoconfig\n")
                    file.write("!\n")
                 
                #Configuration de bgp
                if router == "R1" or router == "R4": 
                    neighbor_AS = list(intent[AS]['router'])
                    file.write(f"router bgp {intent[AS]['bgp']}\n")
                    file.write(f" bgp log-neighbor-changes\n")
                    file.write(" redistribute connected\n")
                    for neighbor in intent[AS]['router'][router]['ebgp_neighbors']:
                        if neighbor == "R":
                            continue
                        adresse_loopback = loopback(intent[AS]['address_loopback'],neighbor[-1])
                        
                        file.write(f" neighbor {adresse_loopback} remote-as {intent[AS]['bgp']}\n")
                        file.write(f" neighbor {adresse_loopback} update-source Loopback0 \n")
                    file.write(" !\n")
                    file.write(f" address-family vpnv4\n")
                    for neighbor in liste_extreme_AS_mid:
                        if router == neighbor:
                            continue
                        adresse_loopback = loopback(intent[AS]['address_loopback'],neighbor[-1])
                        file.write(f"  neighbor {adresse_loopback} activate\n")
                        file.write(f"  neighbor {adresse_loopback} send-community both\n")
                        file.write(f"  neighbor {adresse_loopback} next-hop-self\n")
                    file.write(f" exit-address-family\n")
                    file.write(" !\n")

                    if 'externe' in intent[AS]['router'][router]:
                        i=1
                        for router_other in intent[AS]['router'][router]['externe']:
                            for other_AS in intent:
                                if other_AS == AS:
                                    continue
                                if router_other in intent[other_AS]['router']:
                                    file.write(f" address-family ipv4 vrf Client_{i}\n")
                                    file.write(f"  redistribute connected \n")
                                    file.write(f"  neighbor {ipv4(intent[other_AS]['address'][0],str(2))} remote-as {intent[other_AS]['bgp']}\n")
                                    file.write(f"  neighbor {ipv4(intent[other_AS]['address'][0],str(2))} activate\n")
                                    file.write(" exit-address-family\n")
                                    
                                    if i == 1 :
                                        file.write(" !\n")
                                    elif i == 2 : 
                                        file.write(f"!\n")
                                    i+=1
                    
                
                #Configuration de la redistribution
                if AS != "AS_mid":
                    file.write(f"router bgp {intent[AS]['bgp']}\n")
                    file.write(" bgp log-neighbor-changes\n")
                    file.write(" redistribute connected\n")

                    for router in intent[AS]['router']:
                        externes = intent[AS]['router'][router].get('externe', {})
                        for voisin, interface in externes.items():
            # Cherche le voisin dans les autres AS
                            for AS_other in intent:
                                if AS_other != AS and voisin in intent[AS_other]['router']:
                    # On suppose que l'adresse IP à utiliser est basée sur l'adresse du lien
                                    ip = ipv4(intent[AS]['address'][0], str(1))  # À adapter si tu veux calculer dynamiquement
                                    file.write(f" neighbor {ip} remote-as {intent[AS_other]['bgp']}\n")

                    file.write("!\n")
    
    #send_config_to_router("127.0.0.1", 5000, fichier)



def deploy_to_gns3(router_name, AS, project_path):
    # Ex: router_name = 'R1' => fichier = i1_startup-config.cfg
    router_index = router_name[1:]
    cfg_file = f"i{router_index}_startup-config.cfg"
    
    # Correspondance dossier GNS3 (ex: R1-0)
    gns3_router_folder = intent[AS]['router'][router_name].get('file', {})

    # Dossier config dans le projet GNS3
    target_path = os.path.join(project_path, "project-files", "dynamips", gns3_router_folder, "configs")
    
    # Crée le dossier s’il n'existe pas
    os.makedirs(target_path, exist_ok=True)
    
    # Chemin complet du fichier destination
    dest_file = os.path.join(target_path, f"i{router_index}_startup-config.cfg")

    # Copie le fichier généré dans le dossier de GNS3
    shutil.copy(cfg_file, dest_file)
    print(f"{cfg_file} copié vers {dest_file}")

def main(intent, base_server_config):
    global nombre_router_AS
    liste_extreme_AS_mid = ["R1","R4"]
    for AS in intent:
        nombre_router_AS = 1
        for router in intent[AS]["router"]:
            create_cfg_config(base_server_config, router, intent, AS,liste_extreme_AS_mid)
            deploy_to_gns3(router, AS, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    base_server_config = [
        "version 15.2",
        "service timestamps debug datetime msec",
        "service timestamps log datetime msec",
        "boot-start-marker",
        "boot-end-marker",
        "no aaa new-model",
        "no ip icmp rate-limit unreachable",
        "ip cef",
        "no ip domain lookup",
        "no ipv6 cef",
        "multilink bundle-name authenticated",
        "ip tcp synwait-time 5",
        "ip forward-protocol nd",
        "no ip http server",
        "no ip http secure-server",
        "control-plane",
        "line con 0",
        " exec-timeout 0 0",
        " privilege level 15",
        " logging synchronous",
        " stopbits 1",
        "line aux 0",
        " exec-timeout 0 0",
        " privilege level 15",
        " logging synchronous",
        " stopbits 1",
        "line vty 0 4",
        " login",
        "end"
    ]

    intent = read_json("router.json")
    if intent:
        main(intent, base_server_config)


 
