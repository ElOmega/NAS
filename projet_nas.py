import json

def ipv4(adresse_ip,number):
    adresse_ip = adresse_ip.split('/')
    adresse_ip = adresse_ip[0]
    adresse_ip = adresse_ip +"."+ number +" "+"255.255.255.252"
    return adresse_ip


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

def create_cfg_config(base_server_config, router, intent, AS):
    with open(f'i{router[1:]}_startup-config.cfg', 'w') as file:
        number=router[1:]
        for sentence in base_server_config:
            file.write(sentence + '\n!\n')
            protocol=intent[AS]['protocol']
            ebgp_neighbor=False
            if sentence == "service timestamps log datetime msec":
                file.write(f"hostname {router}\n")
            elif sentence == "ip tcp synwait-time 5":
                #mise en place de l'interface loopback
                loopback_addr = intent[AS]['address_loopback']
                loopback_addr = loopback_addr[0].split('/')
                loopback = loopback_addr[0]+"."+number

                file.write(f"interface Loopback0\n ip address {loopback} 255.255.255.255\n")
                file.write(" ip ospf 1 area 0\n")
                file.write("!\n")

                # Configuration des interfaces
                # for router_id, branche in intent[AS]['router'][router].items():
                #     file.write(f"interface {branche}\n ip address \n")
                #     file.write(" ipv6 ospf 4 area 2\n")
                #     file.write(" negotiation auto\n mpls ip\n")
                #     file.write("!\n")

                #IPV4
                for router_other in intent[AS]['router'][router]:
                    if router_other == "ebgp_neighbors":
                        continue

                    file.write(f"interface {intent[AS]['router'][router][router_other]}\n ip address {ipv4(intent[AS]["address"][0],number)}\n")
                    file.write(" ip ospf 1 area 0\n")
                    file.write(" negotiation auto\n mpls ip\n")

                    file.write("!\n")


                print(number)

                #CONFIGURATION OSPF
                file.write("router ospf 1\n")
                file.write(f" router-id {str(number)+"."+str(number)+"."+str(number)+"."+str(number)}\n")
                file.write(" mpls ldp autoconfig\n")
                file.write("!\n")




                #CONFIG BGP
                # as_number = intent[AS]["AS_number"]
                # router_id = f"{router[1:]}.{router[1:]}.{router[1:]}.{router[1:]}"
                # file.write(f" router bgp {as_number}\n bgp router-id {router_id}\n bgp log-neighbor-changes\n no bgp default ipv4-unicast\n")
                # neighbors_list = []
                # if 'ebgp_neighbors' in intent[AS]['router'][router]:
                #     neighbors = intent[AS]['router'][router]['ebgp_neighbors']
                #     if len(neighbors) > 2:
                #         neighbors=neighbors.split(',')
                #         for i in neighbors:
                #             loopback_addr = loopback_addr[0]+"."+str(i[1])
                #             file.write(f" neighbor {loopback_addr} remote-as {as_number}\n")
                #             file.write(f" neighbor {loopback_addr} update-source Loopback0\n")
                #             file.write(f" neighbor {loopback_addr} next-hop-self\n")
                #     else:


                #         loopback_addr = loopback_addr[0]+"."+str(neighbors[1])
                #         file.write(f" neighbor {loopback_addr} remote-as {as_number}\n")
                #         file.write(f" neighbor {loopback_addr} update-source Loopback0\n")
                #         file.write(f" neighbor {loopback_addr} next-hop-self\n")
                #         neighbors_list.append(loopback_addr)
                
                # # Configuration eBGP avec les routeurs des AS voisins
                # ebgp_neighbors = intent[AS]['router']['ebgp_neighbors']
                # if len(ebgp_neighbors) > 2:
                #     ebgp_neighbors = ebgp_neighbors.split(',')
                
                # for neighbor in ebgp_neighbors:
                #     neighbor_as = None
                #     for other_as in intent:
                #         if other_as != AS and neighbor in intent[other_as]['router']:
                #             neighbor_as = intent[other_as]["AS_number"]
                #             break
                #     if neighbor_as:
                #         file.write(f" neighbor {neighbor_ip.split('/')[0]} remote-as {neighbor_as}\n")
                #         neighbors.append(neighbor_ip.split('/')[0])
                #         ebgp_neighbor=True
                

                # file.write(" address-family ipv4\n")
            #     file.write(" exit-address-family\n !\n")
            #     file.write(" address-family ipv6\n")
            #     if ebgp_neighbor :
            #         for network in intent[AS]['address']:
            #             file.write(f"  network {network}\n")
            #     for neighbors in neighbors_list:
            #         file.write(f"  neighbor {neighbors} activate\n")
                
            #     file.write(" exit-address-family\n!\n")


            # elif sentence == "no ip http secure-server":
            #     router_id=f"{router[1:]}.{router[1:]}.{router[1:]}.{router[1:]}"
            #     file.write(f"ipv6 router ospf 4\n router-id {router_id} \n!\n")



            


def main(intent, base_server_config):
    for AS in intent:
        for router in intent[AS]["router"]:
            create_cfg_config(base_server_config, router, intent, AS)

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


                        # # Configuration iBGP avec tous les routeurs du même AS
                # for peer in intent[AS]['router']:
                #     if peer != router:
                #         peer_loopback = intent[AS]['router'][peer].get("Loopback0", "")
                #         if peer_loopback:
                #             peer_ip = peer_loopback.split('/')[0]
                #             file.write(f" neighbor {peer_ip} remote-as {as_number}\n")
                #             file.write(f" neighbor {peer_ip} update-source Loopback0\n")
                #             file.write(f" neighbor {peer_ip} next-hop-self\n")

                #             neighbors.append(peer_ip)
