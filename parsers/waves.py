import re


def parse_waves_comment(comment: str) -> tuple:
    """ Парсит комментарий Waves.txt

    :param comment: строка комментария
    :return: (values, headers)
    """

    headers = []
    values = []

    headers.append('Тип стратегии')
    values.append(comment.split(': ', maxsplit=1)[0])

    headers.append('Пара')
    par_index = comment.find("DailyVol")
    values.append(comment.split(': ', maxsplit=1)[1][:par_index])

    headers.append('DailyVol')
    daile_index = comment.find("HourlyVol")
    values.append(comment.split(': ', maxsplit=1)[1][par_index:daile_index].strip().split(": ")[1].split()[0])

    tmp = comment[comment.find('CPU'):]

    '''min_index = comment.find("Min")
    stop_index = comment.find("CPU")
    for i in comment[min_index:stop_index].split("% "):
        if len(i.split(" = ")) > 1:
            headers.append(i.split(" = ")[0].strip())
            values.append(i.split(" = ")[1] + "%")'''

    cpu_index = tmp.find('Sys')
    headers.append("CPU")
    values.append(tmp[:cpu_index].strip().split(': ')[1])

    sys_index = tmp.find('AppL')
    headers.append("Sys")
    values.append(tmp[cpu_index:sys_index].strip().split(': ')[1])

    appl_index = tmp.find('API Req')
    headers.append("AppLatency")
    values.append(tmp[sys_index:appl_index].strip().split(': ')[1])

    req_index = tmp.find('API Orders')
    headers.append("API Req")
    values.append(tmp[appl_index:req_index].strip().split(': ')[1])

    orders_index = tmp.find('PriceLag')
    headers.append("API Orders")
    values.append(tmp[req_index:orders_index].strip().split(': ')[1])

    pricelag_index = tmp.find('(RAY Price')
    headers.append("PriceLag")
    values.append(tmp[orders_index:pricelag_index].strip().split(': ')[1])

    view_pricelag_index = tmp.find(' Latency')
    headers.append("Вид PriceLag")
    values.append(tmp[pricelag_index - 6:view_pricelag_index])

    latency_index = tmp.find('Ping')
    headers.append("Latency")
    values.append(tmp[view_pricelag_index:latency_index].strip().split(': ')[1])

    headers.append("Ping")
    values.append(tmp[latency_index:].strip().split(': ')[1])

    #print(tmp, "-------------------", values, headers)
    return values, headers