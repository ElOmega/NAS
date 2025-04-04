import json

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

    with open(f'i{router[-1]}_startup-config.cfg', 'w') as file:
        number=router[-1]
        for sentence in base_server_config:
            file.write(sentence + '\n!\n')
            if sentence == "boot-end-marker" and 'externe' in intent[AS]['router'][router]:
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
                            nombre_router_AS+=1
                    elif position == "externe":
                        for other_AS in intent:
                            if other_AS == AS:
                                continue
                            for router_other in intent[other_AS]['router']:
                                if router_other == router or router not in intent[other_AS]['router'][router_other]:
                                    continue
                                file.write(f"interface {intent[AS]['router'][router]['externe'][router_other]}\n")
                                file.write(f" ip address {ipv4(intent[other_AS]['address'][0],str(2))} 255.255.255.252\n")
                                file.write(" ip ospf 1 area 0\n")
                                file.write(" negotiation auto\n mpls ip\n")
                                file.write("!\n")
                    
                    else : 

                        for router_other in intent[AS]['router'][router]: 
                            file.write(f"interface {intent[AS]['router'][router][router_other]}\n" 
                               f" ip address {ipv4(intent[AS]['address'][0],str(nombre_router_AS))}\n")
                            file.write(" ip ospf 1 area 0\n")
                            file.write(" negotiation auto\n mpls ip\n")
                            file.write("!\n")





                #CONFIGURATION OSPF
                if AS == "AS_mid":
                    file.write("router ospf 1\n")
                    file.write(f" router-id {str(number)+'.'+str(number)+'.'+str(number)+'.'+str(number)}\n")
                    file.write(" mpls ldp autoconfig\n")
                    file.write("!\n")
                 
                #Configuration de bgp
                if router == "R1" or router == "R4": 
                    neighbor_AS = list(intent[AS]['router'])
                    file.write(f"router bgp {intent[AS]['bgp']}\n")
                    file.write(f" bgp log-neighbor-changes\n")
                    for neighbor in intent[AS]['router'][router]['interne']:
                        adresse_loopback = loopback(intent[AS]['address_loopback'],neighbor[-1])
                        file.write(" redistribute connected\n")
                        file.write(f" neighbor {adresse_loopback} remote-as {intent[AS]['bgp']}\n")
                    file.write("!\n")
                    file.write(f"address-family vpnv4\n")
                    for neighbor in liste_extreme_AS_mid:
                        if router == neighbor:
                            continue
                        adresse_loopback = loopback(intent[AS]['address_loopback'],neighbor[-1])
                        file.write(f" neighbor {adresse_loopback} activate\n")
                        file.write(f" neighbor {adresse_loopback} send-community both\n")
                        file.write(f" neighbor {adresse_loopback} next-hop-self\n")
                    file.write(f"exit-address-family\n")
                    file.write("!\n")

                    if 'externe' in intent[AS]['router'][router]:
                        i=1
                        for router_other in intent[AS]['router'][router]['externe']:
                            for other_AS in intent:
                                if other_AS == AS:
                                    continue
                                if router_other in intent[other_AS]['router']:
                                    file.write(f"address-family ipv4 vrf Client_{i}\n")
                                    file.write(f"neighbor {ipv4(intent[other_AS]['address'][0],str(1))} remote-as {intent[other_AS]['bgp']}\n")
                                    file.write(f" neighbor {ipv4(intent[other_AS]['address'][0],str(1))} activate\n")
                                    file.write(" exit-address-family\n")
                                    i+=1
                                    file.write("!\n")
                
                #Configuration de la redistribution
                if AS !="AS_mid":
                    file.write(f"router bgp {intent[AS]['bgp']}\n")
                    file.write(" bgp log-neighbor-changes\n")
                    file.write(" redistribute connected\n")
                    for AS_other in intent :
                            (list(intent[AS]['router'][router])[0])
                            
                            if list(intent[AS]['router'][router])[0] in list(intent[AS_other]['router']):
                                file.write(f" neighbor {ipv4(intent[AS]['address'][0],str(2))} remote-as {intent[AS_other]['bgp']}\n")
                    file.write("!\n")




                            








def main(intent, base_server_config):
    global nombre_router_AS
    liste_extreme_AS_mid = ["R1","R4"]
    for AS in intent:
        nombre_router_AS = 1
        for router in intent[AS]["router"]:
            create_cfg_config(base_server_config, router, intent, AS,liste_extreme_AS_mid)

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


 
