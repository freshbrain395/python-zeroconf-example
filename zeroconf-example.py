import zeroconf
import socket
import threading
import time


def get_local_ip():
    """
    获取本地机器的局域网 IP 地址。
    如果无法获取，则返回回环地址 "127.0.0.1"。
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # 连接到公共 DNS 服务器，不需要实际发送数据
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
    return ip


def register_service(service_name, service_type, port, ip_address=None):
    """
    注册一个 mDNS 服务。

    参数:
    - service_name: 服务的实例名称（例如 "test-service"）。
    - service_type: 服务类型（例如 "_http._tcp.local."）。
    - port: 服务的端口号。
    - ip_address: 服务绑定的 IP 地址。如果未提供，将自动获取本地 IP。

    返回:
    - zeroconf_instance: 注册服务的 Zeroconf 实例。
    - info: ServiceInfo 对象，包含服务的详细信息。
    """
    if ip_address is None:
        ip_address = get_local_ip()

    # 获取本地主机名，并确保格式正确
    hostname = socket.gethostname()
    server = f"{hostname}.local."

    # 创建 Zeroconf 实例
    zeroconf_instance = zeroconf.Zeroconf()

    # 创建 ServiceInfo 对象，包含服务的详细信息
    info = zeroconf.ServiceInfo(
        service_type,
        f"{service_name}.{service_type}",
        addresses=[socket.inet_aton(ip_address)],
        port=port,
        properties={},
        server=server
    )

    # 注册服务
    try:
        zeroconf_instance.register_service(info)
        print(f"服务 '{service_name}' 已注册在 {ip_address}:{port}")
    except Exception as e:
        print(f"无法注册服务 '{service_name}': {e}")
        zeroconf_instance.close()
        return None, None

    return zeroconf_instance, info


class MyListener(zeroconf.ServiceListener):
    def __init__(self, services):
        self.services = services

    def add_service(self, zeroconf_instance, service_type, name):
        info = zeroconf_instance.get_service_info(service_type, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            self.services[name] = {
                "addresses": addresses,
                "port": info.port
            }
            # print(f"发现服务: {name}, 地址: {self.services[name]['addresses']}, 端口: {self.services[name]['port']}")

    def remove_service(self, zeroconf_instance, service_type, name):
        # print(f"服务 {name} 已移除")
        pass

    def update_service(self, zeroconf_instance, service_type, name):
        # print(f"服务 {name} 已更新")
        pass


def discover_services(service_type, duration=5):
    """
    发现指定类型的 mDNS 服务。

    参数:
    - service_type: 要发现的服务类型（例如 "_http._tcp.local."）。
    - duration: 发现的持续时间（秒）。

    返回:
    - services: 发现的服务字典，键为服务名称，值为包含地址和端口的字典。
    """
    zeroconf_instance = zeroconf.Zeroconf()
    services = {}

    # 创建监听器对象
    listener = MyListener(services)

    # 创建服务浏览器
    browser = zeroconf.ServiceBrowser(zeroconf_instance, service_type, listener)
    print(f"开始发现服务类型: {service_type}，持续时间: {duration} 秒...")
    time.sleep(duration)
    zeroconf_instance.close()
    print("服务发现完成。")

    return services


def test_mdns():
    """
    测试 mDNS 服务的注册和发现功能。
    """
    # 服务详细信息
    service_name = "test-service"
    service_type = "_http._tcp.local."
    service_port = 8080
    service_ip = get_local_ip()

    # 注册服务
    print(f"正在注册服务: {service_name}")
    zeroconf_instance, info = register_service(service_name, service_type, service_port, ip_address=service_ip)

    if not zeroconf_instance or not info:
        print("服务注册失败，退出测试。")
        return

    # 创建一个线程用于发现服务
    discovery_results = {}
    discovery_duration = 2  # 发现持续时间（秒）

    def discovery_thread_func():
        discovered = discover_services(service_type, duration=discovery_duration)
        discovery_results.update(discovered)

    discovery_thread = threading.Thread(target=discovery_thread_func, daemon=True)
    discovery_thread.start()

    # 等待发现线程完成
    discovery_thread.join()

    # 取消注册服务
    # print(f"正在取消注册服务: {service_name}")
    # try:
    #     zeroconf_instance.unregister_service(info)
    #     print(f"服务 '{service_name}' 已取消注册。")
    # except Exception as e:
    #     print(f"无法取消注册服务 '{service_name}': {e}")
    # finally:
    #     zeroconf_instance.close()

    # 打印发现结果
    print("发现的服务列表:")
    for name, details in discovery_results.items():
        print(f" - {name}: 地址: {details['addresses']}, 端口: {details['port']}")


if __name__ == "__main__":
    test_mdns()



